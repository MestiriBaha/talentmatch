from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import UserSerializer
from datetime import datetime
from django.contrib import auth
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.utils import timezone
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import render
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.neighbors import NearestNeighbors
import pandas as pd
import textdistance
from sklearn.metrics.pairwise import cosine_similarity
from django import template
from django.contrib import messages
from django.contrib.auth.models import User

@api_view(['POST'])
def create_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return redirect('home.html')
    return render(request, 'signup.html')
def signup(request):
    if request.method == 'POST':
        # Get form data
        
        email = request.POST['email']
        password1 = request.POST.get('password')
        password2 = request.POST.get('confirm_password')

        # Check if passwords match
        if password1 != password2:
            messages.error(request, "Passwords don't match")
            return redirect('signup')
        
        # Create the user
        user = User.objects.create_user(username=email, password=password1, last_login=datetime.now())
        user.last_login = timezone.now()
        user.save()

        # Login the user
        #auth.login(request, user)

        # Redirect to homepage
        return redirect('home')

    return render(request, 'signup.html')
def login(request):
    return render(request, 'login.html') 
def welcome(request):
    return render(request, 'welcome.html')    
def home(request):
    return render(request, 'home.html')   
def jobform(request):
    return render(request, 'jobform.html')      
@csrf_protect     
def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('login')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})    
    else:
        
        return render(request, 'login.html',{'error': 'Invalid email or password.'})     

User = get_user_model()

def login_view2(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return redirect('login')
        
        if user.check_password(password):
            # Login successful
            return redirect('home')
        else:
            return redirect('login')
    
    # If the request method is not POST, render the login template
    return render(request, 'login.html') 






def recommend(request):
    if request.method == 'POST':
        # Read programs and jobs data from CSV files
        df_program = pd.read_csv('users/talentm_data_prog.csv')
        df_jobs = pd.read_csv('users/jobs_talentm.csv')
        
        # Get user input
        selected_option = request.POST['option1']
        user_skills = request.POST['skills']
        print(selected_option)
        
        # Add user skills to df_program
        df_program.loc[df_program['option'] == selected_option, 'skills'] += ',' + user_skills
        
        # Vectorize program and job skills using TF-IDF
        vectorizer = TfidfVectorizer()
        programs_tfidf = vectorizer.fit_transform(df_program['skills'])
        jobs_tfidf = vectorizer.transform(df_jobs['skills'])
        
        # Perform dimensionality reduction using TruncatedSVD
        n_components = 50
        svd = TruncatedSVD(n_components=n_components)
        programs_svd = svd.fit_transform(programs_tfidf)
        jobs_svd = svd.transform(jobs_tfidf)
        
        # Get the row for the selected option
        program_row = df_program[df_program['option'] == selected_option].iloc[0]
        
        # Create list to store missing skills
        missing_skills_list = []
            
        # Loop through each job
        for job_num in range(1, 6):
            # Get job skills
            job_skills = df_jobs['skills'][job_num].split(',')
            
            # Loop through each job skill
            for skill in job_skills:
                similar = False
                for prog_skill in program_row['skills'].split(','):
                    similarity = textdistance.levenshtein.normalized_similarity(skill.strip(), prog_skill.strip())
                    if similarity >= 0.2:
                        similar = True
                        break
                
                if not similar:
                    missing_skills_list.append(skill.strip())
        
        # Remove duplicates from missing skills
        missing_skills = list(set(missing_skills_list))
        
        # Assign recommended skills list to "recommended_skills" column of dataframe
        program_row['recommended_skills'] = ', '.join(missing_skills)
        
        # Calculate similarity between program and jobs
        similarity_vector = cosine_similarity(programs_svd[program_row.name].reshape(1, -1), jobs_svd)
        similarity_scores = similarity_vector[0]
        
        # Get indices of top 3 recommended jobs
        top_job_indices = similarity_scores.argsort()[-6:][::-1]
        
        # Get top 3 recommended jobs' titles and descriptions
        #recommended_jobs_titles = df_jobs.loc[top_job_indices, 'job_title'].tolist()

        # Get top 5 recommended jobs' titles, descriptions, and ids
        recommended_jobs = df_jobs.loc[top_job_indices, ['job_title', 'company', 'skills']]
        
        



        # Get the row index of the option
        option_index=df_program.index[df_program['option'] == selected_option][0]


        # Get program skills for the option
        program_skills = df_program.loc[option_index, 'skills'].split(',')

        # Create list to store missing skills
        missing_skills_list = []

        # Loop through each job
        for job_num in range(1, 6):
            # Get job skills
            job_skills = df_jobs['skills'][job_num].split(',')
    
            # Loop through each job skill
            for skill in job_skills:
                similar = False
                for prog_skill in program_skills:
                    similarity = textdistance.levenshtein.normalized_similarity(skill.strip(), prog_skill.strip())
                    if similarity >= 0.2:
                        similar = True
                        break
        
                if not similar:
                     missing_skills_list.append(skill.strip())

        # Remove duplicates from missing skills
        missing_skills = list(set(missing_skills_list))

        # Matching Rate
        # Calculate similarity between programs and jobs
        similarity_matrix = cosine_similarity(programs_svd, jobs_svd)
        df_program['rate'] = (similarity_matrix.max(axis=1) * 100).astype(int)

        #context = {'recommended_jobs': recommended_jobs}
        context = {'rate': df_program.at[option_index, 'rate'],'recommended_jobs': recommended_jobs, 'missing_skills': missing_skills}
        

        # Pass the recommended jobs list to the template
        return render(request, 'result.html', context)
    
    # Render the index page for GET requests
    return render(request, 'jobform.html') 


def recommend2(request):
    if request.method == 'POST':
        # Read programs and jobs data from CSV files
        df_program = pd.read_csv('users/talentm_data_prog.csv')
        df_jobs = pd.read_csv('users/jobs_talentm.csv')
        final = pd.read_csv('users/final_programs.csv')

        
        
        # Get user input
        selected_option = request.POST['option1']
        user_skills = request.POST['skills']
        print(selected_option)

        option_index = df_program.index[df_program['option'] == selected_option].tolist()[0]
        print(option_index)
        
        # Add user skills to df_program
        df_program.loc[df_program['option'] == selected_option, 'skills'] += ',' + user_skills
        
        # Vectorize program and job skills using TF-IDF
        vectorizer = TfidfVectorizer()
        programs_tfidf = vectorizer.fit_transform(df_program['skills'])
        jobs_tfidf = vectorizer.transform(df_jobs['skills'])
        
        # Perform dimensionality reduction using TruncatedSVD
        n_components = 50
        svd = TruncatedSVD(n_components=n_components)
        programs_svd = svd.fit_transform(programs_tfidf)
        jobs_svd = svd.transform(jobs_tfidf)
        
        # Get the row for the selected option
        program_row = df_program[df_program['option'] == selected_option].iloc[0]
        
        # Create list to store missing skills
        missing_skills_list = []
            
        # Loop through each job
        for job_num in range(1, 6):
            # Get job skills
            job_skills = df_jobs['skills'][job_num].split(',')
            
            # Loop through each job skill
            for skill in job_skills:
                similar = False
                for prog_skill in program_row['skills'].split(','):
                    similarity = textdistance.levenshtein.normalized_similarity(skill.strip(), prog_skill.strip())
                    if similarity >= 0.2:
                        similar = True
                        break
                
                if not similar:
                    missing_skills_list.append(skill.strip())
        
        # Remove duplicates from missing skills
        missing_skills = list(set(missing_skills_list))
        
        # Assign recommended skills list to "recommended_skills" column of dataframe
        program_row['recommended_skills'] = ', '.join(missing_skills)
        
        # Calculate similarity between program and jobs
        similarity_vector = cosine_similarity(programs_svd[program_row.name].reshape(1, -1), jobs_svd)
        similarity_scores = similarity_vector[0]
        
        # Get indices of top 3 recommended jobs
        top_job_indices = similarity_scores.argsort()[-6:][::-1]
        
        # Get top 3 recommended jobs' titles and descriptions
        #recommended_jobs_titles = df_jobs.loc[top_job_indices, 'job_title'].tolist()

        # Get top 5 recommended jobs' titles, descriptions, and ids
        recommended_jobs = df_jobs.loc[top_job_indices, ['job_title', 'company', 'skills']]
        
        



        # Loop through each row of the dataframe
        for index, row in df_program.iterrows():
            # Get program skills
            program_skills = row['skills'].split(',')
    
            # Create list to store missing skills
            missing_skills_list_name = f"missing_skills_{index}"
            globals()[missing_skills_list_name] = []
    
            # Loop through each job
            for job_num in range(1, 6):
                # Get job skills
                job_skills = df_jobs['skills'][job_num].split(',')
        
                # Loop through each job skill
                for skill in job_skills:
                    similar = False
                    for prog_skill in program_skills:
                        similarity = textdistance.levenshtein.normalized_similarity(skill.strip(), prog_skill.strip())
                        if similarity >= 0.2:
                            similar = True
                            break
            
                    if not similar:
                        globals()[missing_skills_list_name].append(skill.strip())
    
            # Remove duplicates from missing skills
            missing_skills = list(set(globals()[missing_skills_list_name]))
    
            # Append missing skills to recommended skills list
            recommended_skills_list_name = f"recommended_skills_{index}"
            globals()[recommended_skills_list_name] = ', '.join(missing_skills)
    
            # Assign recommended skills list to "recommended_skills" column of dataframe
            df_program.at[index, 'recommended_skills'] = ', '.join(list(set(globals()[missing_skills_list_name]))) 

        # Matching Rate
        # Calculate similarity between programs and jobs
        similarity_matrix = cosine_similarity(programs_svd, jobs_svd)
        df_program['rate'] = (similarity_matrix.max(axis=1) * 100).astype(int)


        skills_string = df_program.at[option_index, 'recommended_skills']
        skills_list = skills_string.split(',')

        #context = {'recommended_jobs': recommended_jobs}
        context = {'mrate': final.at[option_index, 'rate'],'recommended_jobs': recommended_jobs, 'skills': skills_list}
        print(option_index)
        print(skills_list)
        # Pass the recommended jobs list to the template
        return render(request, 'result.html', context)
    
    # Render the index page for GET requests
    return render(request, 'jobform.html') 




def missing_skills():
# Loop through each row of the dataframe
    for index, row in df_program.iterrows():
        # Get program skills
        program_skills = row['skills'].split(',')
    
        # Create list to store missing skills
        missing_skills_list_name = f"missing_skills_{index}"
        globals()[missing_skills_list_name] = []
    
        # Loop through each job
        for job_num in range(1, 6):
            # Get job skills
            job_skills = df_jobs['skills'][job_num].split(',')
        
            # Loop through each job skill
            for skill in job_skills:
                similar = False
                for prog_skill in program_skills:
                    similarity = textdistance.levenshtein.normalized_similarity(skill.strip(), prog_skill.strip())
                    if similarity >= 0.2:
                        similar = True
                        break
            
                if not similar:
                    globals()[missing_skills_list_name].append(skill.strip())
    
        # Remove duplicates from missing skills
        missing_skills = list(set(globals()[missing_skills_list_name]))
    
        # Append missing skills to recommended skills list
        recommended_skills_list_name = f"recommended_skills_{index}"
        globals()[recommended_skills_list_name] = ', '.join(missing_skills)
    
        # Assign recommended skills list to "recommended_skills" column of dataframe
        df_program.at[index, 'recommended_skills'] = ', '.join(list(set(globals()[missing_skills_list_name]))) 

def rate():
    #Matching Rate
    # Calculate similarity between programs and jobs
    similarity_matrix = cosine_similarity(programs_svd, jobs_svd)
    df_program['rate'] = (similarity_matrix.max(axis=1) * 100).astype(int)