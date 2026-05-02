from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from election.models import Student


def student_register(request):
    if request.method == "POST":
        student_id = request.POST['student_id']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        course = request.POST['course']
        year_level = request.POST['year_level']
        password = request.POST['password']

        if Student.objects.filter(student_id=student_id).exists():
            messages.error(request, "Student ID already exists.")
            return redirect('student_register')

        Student.objects.create(
            student_id=student_id,
            first_name=first_name,
            last_name=last_name,
            course=course,
            year_level=year_level,
            password=make_password(password)
        )

        messages.success(request, "Registration successful. Please login.")
        return redirect('student_login')

    return render(request, "accounts/register.html")

def student_login(request):
    if request.method == "POST":
        student_id = request.POST['student_id']
        password = request.POST['password']

        try:
            student = Student.objects.get(student_id=student_id)
        except Student.DoesNotExist:
            messages.error(request, "Invalid credentials.")
            return redirect('student_login')

        if check_password(password, student.password):
            request.session['student_id'] = student.student_id
            messages.success(request, "Login successful.")
            return redirect('student_dashboard')
        else:
            messages.error(request, "Invalid credentials.")
            return redirect('student_login')

    return render(request, "accounts/login.html")

def logout(request):
    request.session.flush()
    messages.success(request, "Logged out successfully.")
    return redirect('student_login')