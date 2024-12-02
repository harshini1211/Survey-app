
from django.contrib.auth import authenticate, login, logout
from .forms import UserRegistrationForm
from .models import UserProfile
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Survey, Question, Option, Response, Answer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            role = form.cleaned_data['role']
            user.set_password(form.cleaned_data['password'])
            user.save()
            # Create UserProfile
            UserProfile.objects.create(user=user, role=role)
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'survey_app/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            error = "Invalid login credentials"
            return render(request, 'survey_app/login.html', {'error': error})
    return render(request, 'survey_app/login.html')

@login_required
def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    profile = UserProfile.objects.get(user=request.user)
    if profile.role == 'creator':
        # Redirect to Survey Creator dashboard
        return redirect('creator_dashboard')
    else:
        # Redirect to Survey Taker dashboard
        return redirect('taker_dashboard')

from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test

def is_creator(user):
    return UserProfile.objects.get(user=user).role == 'creator'

@login_required
@user_passes_test(is_creator)
def creator_dashboard(request):
    surveys = Survey.objects.filter(creator=request.user)
    return render(request, 'survey_app/creator_dashboard.html', {'surveys': surveys})

@login_required
@user_passes_test(is_creator)
def create_survey(request):
    if request.method == 'POST':
        # Process survey details
        name = request.POST['name']
        description = request.POST['description']
        publish = request.POST.get('publish', 'no')

        # Create the survey
        survey = Survey.objects.create(
            creator=request.user,
            name=name,
            description=description,
            state='published' if publish == 'yes' else 'draft',
            published_date=timezone.now() if publish == 'yes' else None
        )

        # Add questions and options dynamically
        question_number = 1
        while True:
            question_text_key = f'question_text_{question_number}'
            if question_text_key in request.POST:
                question_text = request.POST[question_text_key]
                question_type = request.POST.get(f'question_type_{question_number}', 'radio')

                # Create the question
                question = Question.objects.create(
                    survey=survey,
                    text=question_text,
                    question_type=question_type
                )

                # Add options dynamically
                option_number = 1
                while True:
                    option_key = f'question_{question_number}_option_{option_number}'
                    option_text = request.POST.get(option_key, '').strip()

                    if option_text:
                        # Create the option
                        Option.objects.create(question=question, text=option_text)
                        option_number += 1
                    else:
                        break  # No more options for this question

                question_number += 1
            else:
                break  # No more questions
        return redirect('creator_dashboard')

    return render(request, 'survey_app/create_survey.html')

def is_creator(user):
    return UserProfile.objects.filter(user=user, role='creator').exists()
@login_required
@user_passes_test(is_creator)
def edit_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)
    questions = Question.objects.filter(survey=survey)

    if request.method == 'POST':
        # Update existing questions
        for question in questions:
            # Update question text
            question_text_key = f'question_text_{question.id}'
            if question_text_key in request.POST:
                question_text = request.POST.get(question_text_key).strip()
                if question_text:
                    question.text = question_text
                    question.save()

            # Update question type
            question_type_key = f'question_type_{question.id}'
            if question_type_key in request.POST:
                question_type = request.POST.get(question_type_key).strip()
                if question_type:
                    question.question_type = question_type
                    question.save()

            # Update existing options for this question
            options = Option.objects.filter(question=question)
            for option in options:
                option_text_key = f'option_{question.id}_{option.id}'
                if option_text_key in request.POST:
                    option_text = request.POST.get(option_text_key).strip()
                    if option_text:
                        option.text = option_text
                        option.save()

            # Add new options dynamically
            option_number = len(options) + 1
            while True:
                new_option_key = f'new_option_{question.id}_{option_number}'
                new_option_text = request.POST.get(new_option_key, '').strip()
                if new_option_text:
                    Option.objects.create(question=question, text=new_option_text)
                    option_number += 1
                else:
                    break  # No more new options for this question

        # Add new questions dynamically
        new_question_number = len(questions) + 1
        while True:
            new_question_text_key = f'new_question_text_{new_question_number}'
            if new_question_text_key in request.POST:
                new_question_text = request.POST.get(new_question_text_key).strip()
                if new_question_text:
                    question_type = request.POST.get(f'new_question_type_{new_question_number}', 'radio').strip()
                    new_question = Question.objects.create(
                        survey=survey,
                        text=new_question_text,
                        question_type=question_type
                    )

                    # Add options for the new question
                    new_option_number = 1
                    while True:
                        new_option_key = f'new_option_{new_question_number}_{new_option_number}'
                        new_option_text = request.POST.get(new_option_key, '').strip()
                        if new_option_text:
                            Option.objects.create(question=new_question, text=new_option_text)
                            new_option_number += 1
                        else:
                            break  # No more options for this new question

                    new_question_number += 1
            else:
                break  # No more new questions

        return redirect('creator_dashboard')  # Redirect after successful save

    return render(request, 'survey_app/edit_survey.html', {
        'survey': survey,
        'questions': questions,
    })



@login_required
@user_passes_test(is_creator)
def publish_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)

    # Validate all questions have options before publishing
    for question in survey.question_set.all():
        if question.option_set.count() < 1:
            return redirect('edit_survey', survey_id=survey_id)  # Redirect to edit if invalid

    # Update the survey state to 'published'
    survey.state = 'published'
    survey.save()
    return redirect('creator_dashboard')  # Redirect to the dashboard


@login_required
@user_passes_test(is_creator)
def close_survey(request, survey_id):
    survey = Survey.objects.get(id=survey_id, creator=request.user)
    survey.state = 'closed'
    survey.save()
    return redirect('creator_dashboard')


@login_required
@user_passes_test(is_creator)
def view_results(request, survey_id):
    survey = Survey.objects.get(id=survey_id, creator=request.user)
    responses = Response.objects.filter(survey=survey)
    total_responses = responses.count()
    question_stats = []

    for question in survey.question_set.all():
        options = question.option_set.all()
        option_stats = []
        for option in options:
            count = Answer.objects.filter(question=question, selected_options=option).count()
            percentage = (count / total_responses) * 100 if total_responses > 0 else 0
            option_stats.append({
                'option_text': option.text,
                'count': count,
                'percentage': percentage
            })
        question_stats.append({
            'question_text': question.text,
            'option_stats': option_stats
        })

    return render(request, 'survey_app/view_results.html', {
        'survey': survey,
        'total_responses': total_responses,
        'question_stats': question_stats
    })

def is_taker(user):
    return UserProfile.objects.get(user=user).role == 'taker'

@login_required
@user_passes_test(is_taker)
def taker_dashboard(request):
    """
    Dashboard for survey takers, showing available surveys and completed surveys.
    """
    # Fetch available surveys
    available_surveys = Survey.objects.filter(
        state__in=['published', 'republished']
    ).exclude(
        id__in=Response.objects.filter(
            taker=request.user
        ).exclude(
            survey__state='republished'  # Allow republished surveys to reappear
        ).values_list('survey__id', flat=True)
    ).distinct()

    # Debugging: Check available surveys
    print(f"Available surveys for {request.user.username}:")
    for survey in available_surveys:
        print(f"ID: {survey.id}, Name: {survey.name}, State: {survey.state}, Published Date: {survey.published_date}")

    # Fetch completed surveys
    completed_surveys = Survey.objects.filter(
        response__taker=request.user
    ).distinct()

    return render(request, 'survey_app/taker_dashboard.html', {
        'available_surveys': available_surveys,
        'completed_surveys': completed_surveys,
    })





from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from survey_app.models import Survey, Response, Answer, Option

@login_required
@user_passes_test(lambda user: user.userprofile.role == 'taker')  # Ensure user is a survey taker
def take_survey(request, survey_id):
    try:
        # Fetch the survey
        survey = Survey.objects.get(id=survey_id)

        # Debugging: Confirm the survey details
        print(f"Taker: {request.user.username} is attempting to take Survey ID: {survey_id}, Name: {survey.name}")

        if request.method == 'POST':
            # Debug: Log POST data
            print(f"POST Data: {request.POST}")

            # Create a response for the survey
            response = Response.objects.create(survey=survey, taker=request.user)

            # Process the survey answers
            for question in survey.question_set.all():
                selected_option_ids = request.POST.getlist(f'question_{question.id}')
                if not selected_option_ids:
                    # Handle error if no option is selected
                    error_message = f"You must select at least one option for question: {question.text}"
                    print(f"Error: {error_message}")
                    response.delete()
                    return render(request, 'survey_app/take_survey.html', {'survey': survey, 'error_message': error_message})
                else:
                    # Save answers
                    answer = Answer.objects.create(response=response, question=question)
                    for option_id in selected_option_ids:
                        option = Option.objects.get(id=option_id)
                        answer.selected_options.add(option)

            # Debug: Successful submission
            print(f"Survey {survey_id} successfully completed by {request.user.username}.")
            return redirect('survey_completed')  # Redirect to the completion page

        # Render the survey for the taker
        return render(request, 'survey_app/take_survey.html', {'survey': survey})

    except Survey.DoesNotExist:
        print(f"Error: Survey ID {survey_id} does not exist.")
        return render(request, '404.html', status=404)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return render(request, '500.html', status=500)



@login_required
@user_passes_test(is_taker)
def survey_completed(request):
    return render(request, 'survey_app/survey_completed.html')


@login_required
@user_passes_test(is_creator)
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id, survey__creator=request.user)
    survey_id = question.survey.id
    question.delete()
    return redirect('edit_survey', survey_id=survey_id)

from django.shortcuts import get_object_or_404, redirect
from .models import Question, Option
@login_required
@user_passes_test(is_creator)
def delete_question(request, survey_id, question_id):
    question = get_object_or_404(Question, id=question_id, survey_id=survey_id)

    if request.method == 'POST':
        question.delete()
        return redirect('edit_survey', survey_id=survey_id)

from django.shortcuts import get_object_or_404, redirect
from .models import Survey, Question, Option

@login_required
@user_passes_test(is_creator)
def add_question(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)

    if request.method == 'POST':
        # Get the question data from the form
        question_text = request.POST.get('question_text', '').strip()
        question_type = request.POST.get('question_type', 'radio').strip()

        # Dynamically collect all options
        options = []
        option_number = 1
        while True:
            option_key = f'option{option_number}'
            option_text = request.POST.get(option_key, '').strip()
            if option_text:
                options.append(option_text)
                option_number += 1
            else:
                break  # Stop when no more options are found

        # Validate inputs
        if question_text and len(options) >= 2:  # Ensure at least 2 options
            # Create the question
            question = Question.objects.create(
                survey=survey,
                text=question_text,
                question_type=question_type
            )

            # Create options for the question
            for option_text in options:
                Option.objects.create(question=question, text=option_text)

            return redirect('edit_survey', survey_id=survey_id)
        else:
            # Handle error: Missing question text or insufficient options
            return render(request, 'survey_app/edit_survey.html', {
                'survey': survey,
                'questions': Question.objects.filter(survey=survey),
                'error_message': 'Please provide a valid question and at least 2 options.'
            })

    return redirect('edit_survey', survey_id=survey_id)

from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.http import HttpResponse

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponse("Login successful")
        else:
            return HttpResponse("Invalid credentials")
    return render(request, 'login.html')
@login_required
@user_passes_test(is_creator)
def delete_option(request, survey_id, question_id, option_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)
    question = get_object_or_404(Question, id=question_id, survey=survey)
    option = get_object_or_404(Option, id=option_id, question=question)

    if request.method == 'POST':
        option.delete()
        return redirect('edit_survey', survey_id=survey_id)

    return redirect('edit_survey', survey_id=survey_id)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import UserProfile, Survey, Question, Option, Response, Answer
from django.utils import timezone

def is_creator(user):
    return UserProfile.objects.get(user=user).role == 'creator'

@login_required
@user_passes_test(is_creator)
def edit_question(request, survey_id, question_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)
    question = get_object_or_404(Question, id=question_id, survey=survey)

    if request.method == 'POST':
        # Check which action was submitted
        if 'delete_option' in request.POST:
            # Deleting an option
            option_id = request.POST.get('delete_option')
            option = get_object_or_404(Option, id=option_id, question=question)
            option.delete()
            messages.success(request, 'Option deleted successfully.')
            return redirect('edit_question', survey_id=survey_id, question_id=question_id)

        elif 'action' in request.POST:
            action = request.POST.get('action')

            if action == 'delete_question':
                # Deleting the question
                question.delete()
                messages.success(request, 'Question deleted successfully.')
                return redirect('edit_survey', survey_id=survey_id)

            elif action == 'save_changes':
                # Saving changes to the question
                # Update question text and type
                question.text = request.POST.get('question_text', question.text)
                question.question_type = request.POST.get('question_type', question.question_type)
                question.save()

                # Update existing options
                existing_options = question.option_set.all()

                for option in existing_options:
                    option_key = f'option_{option.id}'
                    if option_key in request.POST:
                        option_text = request.POST.get(option_key)
                        option.text = option_text
                        option.save()

                # Handle new options
                # Collect all form keys that start with 'new_option_'
                new_options = [key for key in request.POST if key.startswith('new_option_')]
                for key in new_options:
                    option_text = request.POST.get(key)
                    if option_text:
                        Option.objects.create(question=question, text=option_text)

                messages.success(request, 'Question updated successfully.')
                return redirect('edit_question', survey_id=survey_id, question_id=question_id)

        # Default redirect if no action matches
        return redirect('edit_question', survey_id=survey_id, question_id=question_id)

    else:
        # Handle GET request
        return render(request, 'survey_app/edit_survey.html', {
            'survey': survey,
            'question': question,
        })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test

def is_creator(user):
    return UserProfile.objects.get(user=user).role == 'creator'

@login_required
@user_passes_test(is_creator)
def edit_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)
    questions = Question.objects.filter(survey=survey)

    if request.method == 'POST':
        # Determine which action to perform based on the form data
        action = request.POST.get('action', '')
        question_id = request.POST.get('question_id')

        if action == 'save_changes' and question_id:
            # Update an existing question
            question = get_object_or_404(Question, id=question_id, survey=survey)
            question.text = request.POST.get('question_text', question.text).strip()
            question.question_type = request.POST.get('question_type', question.question_type)
            question.save()

            # Update existing options
            existing_options = question.option_set.all()
            for option in existing_options:
                option_key = f'option_{option.id}'
                if option_key in request.POST:
                    option_text = request.POST.get(option_key).strip()
                    if option_text:
                        option.text = option_text
                        option.save()

            # Handle deleted options
            options_to_delete = request.POST.getlist('options_to_delete')
            for option_id in options_to_delete:
                option = get_object_or_404(Option, id=option_id, question=question)
                option.delete()

            # Handle new options
            new_options = [key for key in request.POST if key.startswith('new_option_')]
            for key in new_options:
                option_text = request.POST.get(key).strip()
                if option_text:
                    Option.objects.create(question=question, text=option_text)

        elif action == 'delete_question' and question_id:
            # Delete an existing question
            question = get_object_or_404(Question, id=question_id, survey=survey)
            question.delete()

        elif action == 'add_question':
            # Add a new question
            question_text = request.POST.get('new_question_text', '').strip()
            question_type = request.POST.get('new_question_type', 'radio').strip()
            if question_text:
                new_question = Question.objects.create(
                    survey=survey,
                    text=question_text,
                    question_type=question_type
                )

                # Handle options for the new question
                new_options = [key for key in request.POST if key.startswith('new_option_')]
                for key in new_options:
                    option_text = request.POST.get(key).strip()
                    if option_text:
                        Option.objects.create(question=new_question, text=option_text)

        # After processing, refresh the questions list
        questions = Question.objects.filter(survey=survey)

    return render(request, 'survey_app/edit_survey.html', {
        'survey': survey,
        'questions': questions,
    })


@login_required
@user_passes_test(is_creator)
def publish_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)

    # Validate all questions have options before publishing
    for question in survey.question_set.all():
        if question.option_set.count() < 1:
            messages.error(request, 'All questions must have at least one option before publishing.')
            return redirect('edit_survey', survey_id=survey_id)  # Redirect to edit if invalid

    # Update the survey state to 'published'
    survey.state = 'published'
    survey.published_date = timezone.now()
    survey.save()
    messages.success(request, 'Survey published successfully.')
    return redirect('creator_dashboard')  # Redirect to the dashboard

# Other views remain the same or as previously provided


@login_required
@user_passes_test(is_creator)
def republish_survey(request, survey_id):
    """
    Allows a creator to republish a closed survey.
    """
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)

    # Ensure the survey is in a state where it can be republished
    if survey.state == 'closed':  # Only closed surveys can be republished
        survey.state = 'republished'
        survey.published_date = timezone.now()  # Update the published date
        survey.save()

        print(f"Survey {survey.id} has been republished. State: {survey.state}, Published Date: {survey.published_date}")
    else:
        print(f"Survey {survey.id} cannot be republished because it is not closed.")

    return redirect('creator_dashboard')



@login_required
@user_passes_test(is_creator)
def creator_dashboard(request):
    """
    Dashboard for survey creators, showing all their surveys.
    """
    surveys = Survey.objects.filter(creator=request.user)
    return render(request, 'survey_app/creator_dashboard.html', {'surveys': surveys})


def is_creator(user):
    return UserProfile.objects.get(user=user).role == 'creator'


@login_required
@user_passes_test(is_creator)
def republish_survey(request, survey_id):
    """
    Allows a creator to republish a closed survey.
    """
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)

    # Ensure the survey is in a state where it can be republished
    if survey.state == 'closed':  # Only closed surveys can be republished
        survey.state = 'republished'
        survey.published_date = timezone.now()  # Update the published date
        survey.save()
        print(f"Survey {survey.id} has been republished.")  # Debugging
    else:
        print(f"Survey {survey.id} cannot be republished because it is not closed.")  # Debugging

    return redirect('creator_dashboard')





@login_required
@user_passes_test(is_taker)
def view_survey_results(request, survey_id):
    """
    Allows a survey taker to view their own responses and the overall survey results.
    Ensures the percentages for each question sum up to 100%.
    """
    survey = get_object_or_404(Survey, id=survey_id)
    user_response = Response.objects.filter(survey=survey, taker=request.user).first()
    total_responses = Response.objects.filter(survey=survey).count()

    question_stats = []

    for question in survey.question_set.all():
        options = question.option_set.all()
        option_stats = []

        # Total votes for the question
        total_votes_for_question = sum(
            Answer.objects.filter(question=question, selected_options=option).count()
            for option in options
        )

        # Avoid division by zero
        if total_votes_for_question > 0:
            # Calculate percentages for each option
            for option in options:
                total_count = Answer.objects.filter(question=question, selected_options=option).count()
                percentage = (total_count / total_votes_for_question) * 100

                # Check if the current user selected this option
                user_selected = (
                    user_response.answer_set.filter(question=question, selected_options=option).exists()
                    if user_response else False
                )

                option_stats.append({
                    'option_text': option.text,
                    'total_count': total_count,
                    'percentage': round(percentage, 2),  # Rounded to 2 decimal places
                    'user_selected': user_selected
                })
        else:
            # No votes for this question
            for option in options:
                option_stats.append({
                    'option_text': option.text,
                    'total_count': 0,
                    'percentage': 0.0,
                    'user_selected': False
                })

        question_stats.append({
            'question_text': question.text,
            'option_stats': option_stats
        })

    return render(request, 'survey_app/view_survey_results.html', {
        'survey': survey,
        'question_stats': question_stats,
        'user_response': user_response,
        'total_responses': total_responses,
    })
