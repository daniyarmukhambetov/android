from grafen import settings
from . import models, schemas
from auth.jwt import AuthBearer
from .tokens import account_activation_token
import json
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from django.template.loader import render_to_string
from django.contrib.auth.models import Group as Role,Permission
from typing import List
from ninja import Router, File, Form, Header
from ninja.files import UploadedFile
from django.views.decorators.cache import cache_page
from ninja.errors import HttpError

import vimeo
import requests

from ninja.pagination import paginate, PageNumberPagination


app = Router()




@app.get('/json/{lang}',auth=None)
def get_json(request,lang: str):
    items = models.Item.objects.all()
    json = {}
    if(lang == "all"):
        for item in items:
            item_json = {}
            item_json['ru'] = item.translate
            item_json['kz'] = item.translate_kk
            item_json['en'] = item.translate_en
            json[item.field.system_name] = item_json
    elif(lang == "ru"):
        for item in items:
            json[item.field.system_name]=item.translate
    elif(lang == "en"):
        for item in items:
            json[item.field.system_name]=item.translate_en
    elif(lang == "kz"):
        for item in items:
            json[item.field.system_name]=item.translate_kk
    return json


# USER
@app.get('/auth_user',auth=AuthBearer(),response=schemas.UserAuthSchema, tags=["auth"])
def get_auth(request):
    return request.auth

@app.post("/user/send", tags=["auth"])
def send_mail_to(request,email:str = Form(...)):
    
    user = get_object_or_404(models.User,email=email)
    mail_subject = u'\U0001f525' + "РЕГИСТРАЦИЯ в Bilim WAY"
    message = render_to_string('acc_active_email.html', 
    {
        'user': user,
        'uid':urlsafe_base64_encode(force_bytes(user.pk)),
        'token':account_activation_token.make_token(user),
    })
    # email = EmailMessage(mail_subject, message, to=[user.email])
    # email.send()
    
    try:
    	send_mail(
	        mail_subject,
	        message,
	        settings.EMAIL_HOST_USER,
	        [email],
	        fail_silently=False,
	        html_message=message,
    	)
    except:
        raise HttpError(422, "Не получилось отправить почту")
    return True

@app.put("/users/update", tags=["users"])
def update_user(request, payload: schemas.UserUpdateSchemaIn):
    user = request.auth
    list_ = []
    for attr, value in payload.dict().items():
        if(attr=="school_id"):
            if(value):
                list_.append(attr)
                user.school_id = get_object_or_404(models.School, id=value)
        elif(attr=="group_id"):
            if(value):
                for i in value:
                    user.group_id.clear()
                    user.group_id.add(get_object_or_404(models.Group, id=i.get('id')))
        elif(attr=="password"):
            if(value):
                list_.append(attr)
                user.set_password(value)
        elif(attr=="groups"):
            if(value):
                group_role = Role.objects.get(id=value)
                user.groups.add(group_role)
        else:
            if(value):
                list_.append(attr)
            setattr(user, attr, value)
    user.save(update_fields=list_)
    return {"success": True}


@app.get('/users', response=List[schemas.UserSchema], tags=["users"])
#@paginate(PageNumberPagination)
def get_users(request, **kwargs):
    return models.User.objects.all().exclude(id=1)

@app.get('/users_school', response=List[schemas.UserSchemaBySchool], tags=["school_users"])
@paginate
def get_school_users(request, **kwargs): #**kwargs
    my_user = models.User.objects.filter(school_id=request.auth.school_id).order_by('group_id')
    for user in my_user:
        user.update_available()
    return my_user

# this is extra api for availabe courses
@app.get('/available_course', tags=['Available_Courses_Extra_api'])
def get_num_course(request ):
    course_av = models.Course.objects.filter(school_id=request.auth.school_id).count()
    course_pu = models.Course_user.objects.filter(student_id=request.auth).count()
    return {"course_available": course_av-course_pu,'course_purchased':course_pu}

#teachers
@app.get('/teachers', response=List[schemas.UserForLessonSchemaT], tags=["teachers"])
def get_school_teachers(request):
    teachers = models.User.objects.filter(groups__name='teacher', school_id=request.auth.school_id)
    return teachers




@app.get('/users/{user_id}', response=schemas.FullUserSchema, tags=["users"])
def get_user_by_id(request,user_id: int):
    return get_object_or_404(models.User,id=user_id)


# Register user as owner of new school
@app.post("/user", response=schemas.CreateNewSchoolSchema, tags=["users for new school"], auth=None)
def create_user(request, data: schemas.UserCreateSchemaIn):


    user = models.User(email=data.email, first_name=data.first_name, phone=data.phone, is_active=False)  # User is django auth.User
    user.set_password(data.password)
    try:
        mail_subject = u'\U0001f525' + " РЕГИСТРАЦИЯ в Bilim WAY"
        message = render_to_string('acc_active_email.html', {
                'user': user,
                'domain': request.get_host(),
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            # email = EmailMessage(mail_subject, message, to=[user.email])
            # email.send()
        send_mail(
                mail_subject,
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
                html_message=message,
            )
        # return HttpResponse('success', status=200)
    except:
        raise HttpError(422, " не получилось отправить почту!!")

    try:
        user.save()
        group_role = Role.objects.get(name='owner')
        user.groups.add(group_role)
        school = models.School(sub_domen=str(user.id) + ".gografen.com",
                                   school_name=str(user.id) + " gografen" , creator_id=user)
        school.save()
        r = requests.post('https://api.vimeo.com/users/124980362/projects',
                              headers={'Authorization': 'Bearer a8918cf8921e1863c0567a4459ac8fbd'},
                              data={'name': school.id})
        school.vimeo_folder = r.json()['uri'].split('/')[len(r.json()['uri'].split('/')) - 1]
        school.save(update_fields=['vimeo_folder'])
        user.school_id = school
        user.save(update_fields=['school_id'])

    except:
        raise HttpError(422, "Введены неправильные данные(email,password) или существует такая же почта!!!")
    return user


# this is registration page for bilimway students

@app.post("/user_bw", response=schemas.UserCreateSchemaBW, tags=["user_bw"],auth=None)
def create_user(request, data: schemas.UserCreateSchemaBW):
    email=data.email
    if models.User.objects.filter(email=email).exists()==True:
        raise HttpError(404, "почта уже существует")

    user = models.User(email=data.email,first_name=data.first_name,last_name=data.last_name,phone = data.phone,is_active=False) # User is django auth.User
    user.set_password(data.password)

    user.school_id = models.School.objects.get(id=24)
    try:
        user.save()
        group_role = Role.objects.get(name='student')
        user.groups.add(group_role)
        # return HttpResponse(200, "удалось")
    except:
        raise HttpError(404,"Неверная почта или пароль")

    try:
        mail_subject = u'\U0001f525' + "РЕГИСТРАЦИЯ в Bilim WAY"
        message = render_to_string('acc_active_email.html', {
                'user': user,
                'domain': request.get_host(),
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
         })
        send_mail(
                mail_subject,
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
                html_message=message,
            )

    except:
        raise HttpError(422, "Пользователь создан но не получилось отправить почту!!")

def get_request_from_alfacrm():
    url = 'https://bilimway.s20.online/v2api/auth/login'
    api_key = 'fac2d535-c337-11ea-a443-ac1f6b478310'
    email = 'sayat.nurly@bilimedu.kz'
    X_APP_KEY = '81a69fa8d9852527fb794a1f3caf7453'
    headers = {'Accept': 'application/json'}
    data = {"email": email, "password": "celeroN1", "api_key": api_key, 'X-APP-KEY': X_APP_KEY}
    data = json.dumps(data)
    authenticate = requests.post(url, headers=headers, data=data)

    return authenticate

@app.post("/s_user", response=schemas.NewSchemaForSimpleUser, tags=["users"])
def create_simple_user(request , data: schemas.SimpleUserForBilimway):
    get_token = json.loads(get_request_from_alfacrm().text)
    token = get_token['token']
    headers = {
        'X-ALFACRM-TOKEN': f'{token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    # lets check email first
    email=data.email
    if models.User.objects.filter(email=email).exists()==True:
        raise HttpError(422, "почта уже существует")

    user = models.User(email=data.email, first_name=data.first_name, last_name=data.last_name, phone=data.phone,
                           is_active=False)
    user.set_password(data.password)
    user.school_id = request.auth.school_id
    success=False
    if data.alfacrm_id !=0:
        user.alfacrm_id = data.alfacrm_id
        req = requests.post(f"https://bilimway.s20.online/v2api/1/customer/update?id={user.alfacrm_id}", headers=headers)
        if req.status_code==200:
            get_email = json.loads(req.text)
            email_list = get_email['model']['email']
            for item in email_list:
                if item == data.email:
                    my_request = requests.post(
                                f"https://bilimway.s20.online/v2api/1/customer/update?id={user.alfacrm_id}",
                                headers=headers,
                                data=json.dumps({"custom_grafen_password": data.password}))

                    if my_request.status_code==200:
                        user.save()
                        try:
                            user.groups.add(Role.objects.get(id=data.groups))
                        except Role.DoesNotExist:
                            raise HttpError(422, "Роли с ID {} не существует.".format(data.groups))
                        try:
                            mail_subject = u'\U0001f525' + "РЕГИСТРАЦИЯ в " + user.school_id.school_name
                            message = render_to_string('acc_active_email_2.html',
                                                       {
                                                           'user': user,
                                                           'pass': data.password,
                                                           'domain': request.get_host(),
                                                           'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                                                           'token': account_activation_token.make_token(user),
                                                       })
                            send_mail(
                                mail_subject,
                                message,
                                settings.EMAIL_HOST_USER,
                                [user.email],
                                fail_silently=False,
                                html_message=message,
                            )
                        except:
                            raise HttpError(422,
                                            "Пользователь c ID {} создан но не получилось отправить почту на {}.".format(
                                                user.id,
                                                user.email))

                    else:
                        raise HttpError(404, "The ALFA-CRM ID does not correct!")
                else:
                    raise HttpError(404, "The ALFA-CRM email does not correct!")
        else:
            raise HttpError(404, "The ALFA-CRM ID does not correct!.")
    else:
        user.save()
        try:
            user.groups.add(Role.objects.get(id=data.groups))
        except Role.DoesNotExist:
            raise HttpError(422, "Роли с ID {} не существует.".format(data.groups))
        try:
            mail_subject = u'\U0001f525' + "РЕГИСТРАЦИЯ в " + user.school_id.school_name
            message = render_to_string('acc_active_email_2.html',
                                           {
                                               'user': user,
                                               'pass': data.password,
                                               'domain': request.get_host(),
                                               'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                                               'token': account_activation_token.make_token(user),
                                           })
            send_mail(
                    mail_subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [user.email],
                    fail_silently=False,
                    html_message=message,
                )
        except:
            raise HttpError(422, "Пользователь c ID {} создан но не получилось отправить почту на {}.".format(user.id,
                                                                                                                  user.email))


    return user

@app.post('/user/avatar', tags=["users"])
def upload_avatar(request, file: UploadedFile = File(...)):
    user = request.auth
    user.avatar = file
    user.save(update_fields=['avatar'])
    print(user.avatar,file)
    return { "success": True }

@app.put("/users/{user_id}", tags=["users"])
def update_user_by_id(request, user_id: int, payload: schemas.UserUpdateSchemaIn):
    user = get_object_or_404(models.User, id=user_id)
    list_ = []
    for attr, value in payload.dict().items():
    	if(value):
            if(attr=="school_id"):
                list_.append(attr)
                user.school_id = get_object_or_404(models.School, id=value)
            elif(attr=="group_id"):
                user.group_id.clear()
                for i in value:
                    user.group_id.add(get_object_or_404(models.Group, id=i.get('id')))
            elif(attr=="password"):
                list_.append(attr)
                user.set_password(value)
            elif(attr=="groups"):
                group_role = Role.objects.get(id=value)
                user.groups.add(group_role)
            else:
                list_.append(attr)
                setattr(user, attr, value)
    user.save(update_fields=list_)
    return {"success": True}


@app.delete("/users/{user_id}", tags=["users"])
def delete_user(request, user_id: int):
    if(user_id==1):
        raise HttpError(422, "Невозможно удалить модератора!")
    user = get_object_or_404(models.User, id=user_id)
    school = models.School.objects.filter(creator_id=user.id).first()
    if(school):
        school.delete()
    user.delete()
    return {"success": True}


# SCHOOL
@app.get('/schools', response=List[schemas.SchoolSchema], tags=["schools"],auth=AuthBearer())
def get_schools(request):
    school = models.School.objects.all()
    for item in school:
        item.update_total_users()
    return school
@app.get('/school/{school_id}', response=schemas.SchoolSchema, tags=["schools"])
def get_school(request,school_id: int):
    return get_object_or_404(models.School,id=school_id)

@app.post("/schools", response=schemas.SchoolSchema, tags=["schools"])
def create_school(request , data: schemas.SchoolCreateSchema):
    user = get_object_or_404(models.User, id=data.creator_id)
    school = models.School.objects.create(creator_id=user,school_name=data.school_name) 
    school.save()
    
    try:
        raise HttpError(422, r.json())
    except:
        raise HttpError(422, "Введены неправильные данные!!!")
    user.school_id = school
    user.save(update_fields=['school_id'])
    return school

@app.delete("/schools/{school_id}", tags=["schools"])
def delete_school(request, school_id: int):
    school = get_object_or_404(models.School, id=school_id)
    school.delete()
    return {"success": True}

@app.put("/schools/{school_id}", tags=["schools"])
def update_school(request, school_id: int, payload: schemas.SchoolCreateSchema):
    school = get_object_or_404(models.School, id=school_id)
    for attr, value in payload.dict().items():
        if(attr=="creator_id"):
            school.creator_id = get_object_or_404(models.User, id=value)
        else:
            setattr(school, attr, value)
    school.save()
    return {"success": True}

#COURSE
@cache_page(60 * 5) # cache added on this api
@app.get('/courses', response=List[schemas.CourseSchema], tags=["courses"])
def get_courses(request):
    courses =  models.Course.objects.filter(school_id=request.auth.school_id)
    for item in courses:
        item.update_count_users()
        item.update_course_rating()
    return courses

@app.get('/my_courses', response=List[schemas.CourseSchema], tags=["courses"])
def get_my_courses(request):
	'''
	Получает курсы авторизованного пользователя
	'''
	list_ = []
	access = models.Course_user.objects.filter(student_id=request.auth.id)
	for item in access:
		list_.append(models.Course.objects.get(id=item.course_id.id))
	return list_

@app.get('/user_courses/{user_id}', response=List[schemas.CourseSchema], tags=["courses"])
def get_user_courses(request,user_id: int):
	list_ = []
	access = models.Course_user.objects.filter(student_id=user_id)
	for item in access:
		list_.append(models.Course.objects.get(id=item.course_id.id))
	return list_

@app.get('/courses/school', response=List[schemas.CourseSchema], tags=["courses"])
def get_courses_by_school(request):
    '''
    (READ)Request to get all courses by school.
    '''
    courses =  models.Course.objects.filter(school_id=request.auth.school_id)
    
    for course in courses:
        course.update_duration()
        course.update_num_lessons()
    return courses

@app.get('/course/{course_id}', response=schemas.CourseSchema, tags=["courses"])
def get_course(request,course_id:int):
	access = models.Course_user.objects.filter(student_id=request.auth,course_id=course_id)
	access_value = False
	if(access.first()):
		access_value = True
	return get_object_or_404(models.Course,id=course_id)

@app.get('/course/vector/{vector_id}', response=List[schemas.CourseSchema], tags=["courses"], auth=None)
def get_courses_by_vector(request,vector_id:int):
    return models.Course.objects.filter(vector_id__id=vector_id)



@app.post("/course", response=schemas.CourseSchema, tags=["courses"])
def create_course(request , data: schemas.CourseCreateSchema):#
    '''
        end_date: YYYY-MM-DD
    '''
    course = models.Course.objects.create()
    course.title_ru = data.title_ru
    course.title_en = data.title_en
    course.title_kk = data.title_kk
    course.short_desc_ru = data.short_desc_ru
    course.short_desc_en = data.short_desc_en
    course.short_desc_kk = data.short_desc_kk
    course.full_desc_ru = data.full_desc_ru
    course.full_desc_en = data.full_desc_en
    course.full_desc_kk = data.full_desc_kk
    course.cost_ru = data.cost_ru
    course.cost_en = data.cost_en
    course.cost_kk = data.cost_kk
    course.school_id=request.auth.school_id
    course.is_necessary = data.is_necessary
    course.end_date = data.end_date
    for i in data.vector_id:
        course.vector_id.add(models.Vector.objects.filter(id=i.id).first())
    for i in data.teacher_id:
        course.teacher_id.add(models.User.objects.filter(id=i.id).first())
    
    try:
        course.save()
        for t in course.teacher_id.all():
            group = models.Group.objects.create(course_id=course,teacher_id=t)
            group.save()
            t.group_id.add(group)
    except:
        raise HttpError(422, "Не удалось сохранить!")
    
    return course


@app.post('/course/{course_id}/poster/{lang}', tags=["courses"])
def upload_poster(request, course_id: int, lang: str, poster: UploadedFile = File(...)):
    course = get_object_or_404(models.Course, id=course_id)
    if(lang=="ru"):
        course.poster_ru = poster
    elif(lang=="kz"):
        course.poster_kk = poster
    elif(lang=="en"):
        course.poster_en = poster
    else:
        course.poster = poster
        
        
    course.save()
    return { "success": True }

@app.post('/course/{course_id}/mini_poster/{lang}', tags=["courses"])
def upload_mini_poster(request, course_id: int, lang: str, mini_poster: UploadedFile = File(...)):
    course = get_object_or_404(models.Course, id=course_id)
    if(lang=="ru"):
        course.mini_poster_ru = mini_poster
    elif(lang=="kz"):
        course.mini_poster_kk = mini_poster
    elif(lang=="en"):
        course.mini_poster_en = mini_poster
    else:
        course.mini_poster = mini_poster
    course.save()
    return { "success": True }

@app.delete("/courses/{course_id}", tags=["courses"])
def delete_course(request, course_id: int):
    course = get_object_or_404(models.Course, id=course_id)
    vectors = course.vector_id.all()
    course.delete()
    
    return {"success": True}

@app.put("/courses/{course_id}", tags=["courses"])
def update_course(request, course_id: int, payload: schemas.CourseCreateSchema):
    course = get_object_or_404(models.Course, id=course_id)
    list_=[]
    for attr, value in payload.dict().items():
        
        if(attr=="vector_id"):
            course.vector_id.clear()
            if(value):
                for i in value:
                    print(i.get('id'))
                    course.vector_id.add(models.Vector.objects.filter(id=i.get('id')).first())
        elif(attr=="teacher_id"):
            course.teacher_id.clear()
            if(value):
                for i in value:
                    course.teacher_id.add(models.User.objects.filter(id=i.get('id')).first())
        else:
            list_.append(attr)
            setattr(course, attr, value)
    course.save(update_fields=list_)
    for t in course.teacher_id.all():
        group_get,group_save = models.Group.objects.get_or_create(course_id=course,teacher_id=t)
        if(group_get not in t.group_id.all()):
            t.group_id.add(group_get)
    groups = models.Group.objects.filter(course_id=course)
    
    for g in groups:
    	if(g.teacher_id not in course.teacher_id.all()):
    		g.delete()
    return {"success": True}

#LESSON
@app.get('/lessons', response=List[schemas.LessonSchema], tags=["lessons"])
def get_lessons(request):
    return models.Lesson.objects.all()

@app.get('/lessons/school', response=List[schemas.LessonSchema], tags=["lessons"])
def get_lessons_by_school(request):

    return models.Lesson.objects.filter(school_id=request.auth.school_id)

@app.get('/{course_id}/lessons', response=List[schemas.LessonSchema], tags=["lessons"], auth=None)
def get_lessons_by_course(request, course_id: int):
    return models.Lesson.objects.filter(course_id=course_id)

@app.get('/lesson/{lesson_id}', response=schemas.LessonSchema, tags=["lessons"])
def get_lesson(request,lesson_id:int):
    # for item in models.LessonUser.objects.all():
    #     item.update_track() # this is update track of lesson
    return get_object_or_404(models.Lesson,id=lesson_id)

@app.get('/get_project_id', tags=["lessons"])
def get_lesadwson(request,lesson_id:int):
    return request.auth.school_id.vimeo_folder

@app.post('/lesson/{lesson_id}/video/{lang}', tags=["lessons"])
def upload_video(request, lesson_id: int, lang: str, video: UploadedFile = File(...)):
    client = vimeo.VimeoClient(
        token='20d29fd1f79dc96dbb3220ae67277c70',
        key='c4925b8102d19218e4b299606ef5a36ea59f6b96',
        secret='bw0aCT55GdjBDS2k9Iyol3eMT+eCuXCX1kDeul+DP5kgs6oB9ft5uEvDoz7AG6u+nuHVnf6Q6vIH3nV0q7wiBxoQiOS0qVbol/WaQfTAIrO/b9NUcPkd93cEQBV7ARiT'
    )
    lesson = get_object_or_404(models.Lesson, id=lesson_id)
    if(lang=="ru"):
        lesson.video_ru = video
    elif(lang=="kz"):
        lesson.video_kk = video
    elif(lang=="en"):
        lesson.video_en = video
    else:
        lesson.video = video
    
    lesson.save()
    
    if(lang=="ru"):
        path = lesson.video_ru.path
        name = lesson.video_ru.name
    elif(lang=="kz"):
        path = lesson.video_kk.path
        name = lesson.video_kk.name
    elif(lang=="en"):
        path = lesson.video_en.path
        name = lesson.video_en.name
    else:
        path = lesson.video.path
        name = lesson.video.name
    
    uri = client.upload(path, 
    data={
        'name': name,
        'description': 'The description goes here.'
    })
    v_id = uri.split('/')[len(uri.split('/'))-1]
    if(lang=="ru"):
    	lesson.vimeo_id_ru = v_id
    elif(lang=="kz"):
    	lesson.vimeo_id_kk = v_id
    elif(lang=="en"):
    	lesson.vimeo_id_en = v_id
    else:
        lesson.vimeo_id = v_id
    
    client.put(uri + '/privacy/domains/https://'+request.auth.school_id.sub_domen)
    client.patch(uri, data={
      'privacy': {
        'embed': 'whitelist'
      }
    })
    response = client.get(uri)
    lesson.save(update_fields=['vimeo_id','vimeo_id_ru','vimeo_id_en','vimeo_id_kk'])
    user_id=124980362
    project_id=request.auth.school_id.vimeo_folder
    video_id=uri.split('/')[len(uri.split('/'))-1]
    url='https://api.vimeo.com/users/'+str(user_id)+'/projects/'+str(project_id)+'/videos/'+str(video_id)
    r = requests.put(url,headers={'Authorization': 'Bearer a8918cf8921e1863c0567a4459ac8fbd'})
    # 
    return { "success" : True , "url" : url ,"folder" : r.status_code }#,"folder":r.json()

@app.post("/lessons", response=schemas.LessonSchema, tags=["lessons"])
def create_lesson(request , data: schemas.LessonCreateSchema):#
    try:
        # lesson = models.Lesson.objects.create(**data.dict())
        lesson = models.Lesson.objects.create(course_id=get_object_or_404(models.Course,id=data.course_id.id),school_id=request.auth.school_id)
        lesson.title_ru = data.title_ru
        lesson.title_en = data.title_en
        lesson.title_kk = data.title_kk
        lesson.short_desc_ru = data.short_desc_ru
        lesson.short_desc_en = data.short_desc_en
        lesson.short_desc_kk = data.short_desc_kk
        lesson.full_desc_ru = data.full_desc_ru
        lesson.full_desc_en = data.full_desc_en
        lesson.full_desc_kk = data.full_desc_kk
        lesson.duration = data.duration
        lesson.type_of = data.type_of
        lesson.order = data.order
        for i in data.teacher_id:
            lesson.teacher_id.add(models.User.objects.filter(id=i.id).first())
        lesson.save()
        
    except:
        raise HttpError(422, "Введены неправильные данные!!!")
    
    return lesson

@app.delete("/lessons/{lesson_id}", tags=["lessons"])
def delete_lesson(request, lesson_id: int):
    lesson = get_object_or_404(models.Lesson, id=lesson_id)
    course = lesson.course_id
    lesson.delete()
    course.update_duration()
    course.update_num_lessons()
    return {"success": True}

@app.put("/lessons/{lesson_id}", tags=["lessons"])
def update_lesson(request, lesson_id: int, payload: schemas.LessonCreateSchema):
    lesson = get_object_or_404(models.Lesson, id=lesson_id)
    list_=[]
    for attr, value in payload.dict().items():
    	if(value):
	        if(attr=="course_id"):
	            list_.append(attr)
	            lesson.course_id=get_object_or_404(models.Course,id=value.get('id'))
	        elif(attr=="teacher_id"):
	            lesson.teacher_id.clear()
	            for i in value:
	                lesson.teacher_id.add(models.User.objects.filter(id=i.get('id')).first())
	        else:
	            list_.append(attr)
	            setattr(lesson, attr, value)
    lesson.save(update_fields=list_)
    return {"success": True}

#LessonUser
@app.get('/lesson_user/all', response=List[schemas.LessonUserSchema], tags=["LessonUsers"])
def get_all_lesson_user(request):
	#get_all_ = models.LessonUser.objects.filter(student_id=request.auth)
    all_lesson = models.LessonUser.objects.filter(student_id=request.auth)
    for item in all_lesson:
        item.update_track() # this is update track
    return all_lesson

#Track Lesson for Each User
@app.get('/track/{track_id}', tags=['Track Lesson '])
def track_lesson(request, track_id:int):
    user= request.auth
    lesson = get_object_or_404(models.Lesson, id=track_id)
    track = models.TrackLessonUser.objects.create(
        user=user,
        lesson=lesson,
        done=True
    )
    try:
        track.save()
        return {"completed ":True}
    except:
        raise HttpError(404, "the track does not created")



@app.get('/lesson_user/{lesson_id}', response=schemas.LessonUserSchema, tags=["LessonUsers"])
def get_or_create_lesson_user(request,lesson_id: int):
	get, create = models.LessonUser.objects.get_or_create(lesson_id=get_object_or_404(models.Lesson,id=lesson_id),student_id=request.auth)
	if(get):
		return get
	else:
		return create

@app.put("/lesson_user/update/{lu_id}", tags=["LessonUsers"])
def update_lesson_user(request, lu_id: int, payload: schemas.LessonUserUpdateScheme):
    lu = get_object_or_404(models.LessonUser, id=lu_id)
    list_=[]
    for attr, value in payload.dict().items():
    	if(value):
            list_.append(attr)
            setattr(lu, attr, value)
    lu.save(update_fields=list_)
    return {"success": True}
#KnowladgeBase
@app.post("/kb/{type_name}/{type_id}",response=List[schemas.KnowledgeBaseSchema], tags=["knowladgebase"])
def create_knowladge_base(request, type_name: int,type_id:int,files: List[UploadedFile] = File(...)):
   list_ = []
   client = vimeo.VimeoClient(
       token='20d29fd1f79dc96dbb3220ae67277c70',
       key='c4925b8102d19218e4b299606ef5a36ea59f6b96',
       secret='bw0aCT55GdjBDS2k9Iyol3eMT+eCuXCX1kDeul+DP5kgs6oB9ft5uEvDoz7AG6u+nuHVnf6Q6vIH3nV0q7wiBxoQiOS0qVbol/WaQfTAIrO/b9NUcPkd93cEQBV7ARiT'
   )
   for f in files:
       kb = models.KnowledgeBase(name=f.name,files=f,type_name=type_name,type_id=type_id,creator_id=models.User.objects.filter(id=request.auth.id).first())
       kb.save()
       list_.append(kb)
       if(kb.find_typecheck()==1):
           file_name = f
           uri = client.upload(kb.files.path,
           data={
               'name': f.name,
               'description': 'The description goes here.'
           })
           kb.vimeo_id=uri
           kb.save(update_fields=['vimeo_id'])
   return list_


@app.get('/kbs', response=List[schemas.KnowledgeBaseSchema], tags=["knowladgebase"])
def get_knowladge_bases(request):
   return models.KnowledgeBase.objects.all()

@app.get('/kb/{type_name}/{type_id}', response=List[schemas.KnowledgeBaseSchema], tags=["knowladgebase"])
def get_knowladge_base(request, type_name: int,type_id:int):
   return models.KnowledgeBase.objects.filter(type_name=type_name,type_id=type_id)

@app.put("/kb/{kb_id}", tags=["knowladgebase"])
def update_knowladge_base(request, kb_id: int, payload: schemas.KnowledgeBaseSchemaIn):
   kb = get_object_or_404(models.KnowledgeBase, id=kb_id)
   for attr, value in payload.dict().items():
       if(value):
           setattr(kb, attr, value)
   kb.save()
   return {"success": True}

@app.delete("/kb/{kb_id}", tags=["knowladgebase"])
def delete_knowladge_base(request, kb_id: int):
   kb = get_object_or_404(models.KnowledgeBase, id=kb_id)
   kb.delete()
   return {"success": True}

#COMMENT
@app.post("/comment", response=schemas.CommentSchema, tags=["comments"],auth=AuthBearer())
def create_comment(request , data: schemas.CommentSchemaIn):
    # user = get_object_or_404(models.User, id=data.user_id)
    comment = models.Comment.objects.create(user_id=request.auth,course_id=models.Course.objects.filter(id=data.course_id).first(),content=data.content) 
    try:
        comment.save()
    except:
        raise HttpError(422, "Введены неправильные данные!!!")
    return comment

@app.get('/comments', response=List[schemas.CommentSchema], tags=["comments"])
def get_comments(request):
    return models.Comment.objects.all()

@app.get('/comment/{comment_id}', response=schemas.CommentSchema, tags=["comments"])
def get_comment(request,comment_id:int):
    return get_object_or_404(models.Comment,id=comment_id)

@app.put("/comment/{comment_id}", tags=["comments"])
def update_comment(request, comment_id: int, payload: schemas.CommentSchemaIn):
    comment = get_object_or_404(models.Comment, id=comment_id)
    for attr, value in payload.dict().items():
        if(attr=="course_id"):
            if(value):
                comment.course_id=models.Course.objects.filter(id=value).first()
        else:
            setattr(comment, attr, value)
    comment.save()
    return {"success": True}

@app.delete("/comment/{comment_id}", tags=["comments"])
def delete_comment(request, comment_id: int):
    comment = get_object_or_404(models.Comment, id=comment_id)
    comment.delete()
    return {"success": True}

#EXERCISE
@app.post("/exercise", response=schemas.ExerciseSchema, tags=["exercises"],auth=AuthBearer())
def create_exercise(request , data: schemas.ExerciseSchemaIn):
    exercise = models.Exercise.objects.create(creator_id=request.auth,ex_id=models.Exercise_list.objects.filter(id=data.ex_id).first()) 
    # ,text=data.text,desc=data.desc,title=data.title
    exercise.text_ru=data.text_ru
    exercise.text_en=data.text_en
    exercise.text_kk=data.text_kk
    exercise.desc_ru=data.desc_ru
    exercise.desc_en=data.desc_en
    exercise.desc_kk=data.desc_kk
    exercise.title_ru=data.title_ru
    exercise.title_en=data.title_en
    exercise.title_kk=data.title_kk
    exercise.order = data.order
    try:
        exercise.save()
    except:
        raise HttpError(422, "Введены неправильные данные!!!")
    return exercise

@cache_page(60 * 5) # cache added on this api
@app.get('/exercises', response=List[schemas.ExerciseSchema], tags=["exercises"])
def get_exercises(request):
    return models.Exercise.objects.filter(creator_id__school_id=request.auth.school_id).exclude(text__exact='')


@app.get('/exercise/{exercise_id}', response=schemas.ExerciseSchema, tags=["exercises"])
def get_exercise(request,exercise_id:int):
    return get_object_or_404(models.Exercise,id=exercise_id)

# task three
@app.get('/exercise/list/{el_id}', response=List[schemas.ExerciseSchema], tags=["exercises"],auth=None)
def get_exercise_by_exercise_list(request,el_id:int):
    return models.Exercise.objects.filter(ex_id=el_id).exclude(text__exact='')


@app.put("/exercise/{exercise_id}", tags=["exercises"])
def update_exercise(request, exercise_id: int, payload: schemas.ExerciseSchemaIn):
    exercise = get_object_or_404(models.Exercise, id=exercise_id)
    for attr, value in payload.dict().items():
        if(attr=="ex_id"):
            if(value):
                exercise.ex_id=models.Exercise_list.objects.filter(id=value).first()
        else:
            setattr(exercise, attr, value)
    exercise.save()
    return {"success": True}


@app.delete("/exercise/{exercise_id}", tags=["exercises"])
def delete_exercise_list(request, exercise_id: int):
    exercise = get_object_or_404(models.Exercise, id=exercise_id)
    exercise.delete()
    return {"success": True}

#Exercise_list
@app.post("/exercise_list", response=schemas.Exercise_listSchema, tags=["exercise_lists"],auth=AuthBearer())
def create_exercise_list(request , data: schemas.Exercise_listSchemaIn):
    if models.Lesson.objects.filter(id=data.lesson_id).exists()==False:
        raise HttpError(404, f'группы заданий с таким {data.lesson_id} не  существует!')

    else:
        ex_list = models.Exercise_list.objects.create(creator_id=request.auth,lesson_id=models.Lesson.objects.filter(id=data.lesson_id).first())
        if(data.title_ru):
            ex_list.title_ru = data.title_ru
        if(data.title_en):
            ex_list.title_en = data.title_en
        if(data.title_kk):
            ex_list.title_kk = data.title_kk
        try:
            ex_list.save()
        except:
            raise HttpError(422, "Введены неправильные данные!!!")
        return ex_list

@cache_page(60 * 5) # cache added on this api
@app.get('/exercise_lists', response=List[schemas.Exercise_listSchema], tags=["exercise_lists"])
def get_exercise_lists(request):
    return models.Exercise_list.objects.all()

@app.get('/exercise_list/{ex_id}', response=schemas.Exercise_listSchema, tags=["exercise_lists"])
def get_exercise_list(request,ex_id:int):
    return get_object_or_404(models.Exercise_list,id=ex_id)

# task two already done
@app.get('/exercise_list/lesson/{lesson_id}', response=List[schemas.Exercise_listSchema], tags=["exercise_lists"])
def get_exercise_list_by_lesson(request,lesson_id:int):
    return models.Exercise_list.objects.filter(lesson_id=get_object_or_404(models.Lesson,id=lesson_id))

@app.put("/exercise_list/{ex_id}", tags=["exercise_lists"])
def update_exercise_list(request, ex_id: int, payload: schemas.Exercise_listSchemaIn):
    exercise = get_object_or_404(models.Exercise_list, id=ex_id)
    for attr, value in payload.dict().items():
        if(value):
            if(attr=="lesson_id"):
                exercise.lesson_id=models.Lesson.objects.filter(id=value).first()
            else:
                setattr(exercise, attr, value)
    exercise.save()
    return {"success": True}

@app.post('/exercise_list/{ex_id}/file', tags=["exercise_lists"])
def upload_file(request, ex_id: int, file: UploadedFile = File(...)):
    exercise = get_object_or_404(models.Exercise_list, id=ex_id)
    exercise.file = file
    exercise.save(update_fields=['file'])
    return { "success": True }


@app.delete('/exercise_list/{ex_id}/file', tags=["exercise_lists"])
def delete_file(request, ex_id: int):
    exercise = get_object_or_404(models.Exercise_list, id=ex_id)
    exercise.file = ''
    exercise.save(update_fields=['file'])
    return { "success": True }


@app.delete("/exercise_list/{ex_id}", tags=["exercise_lists"])
def delete_exercise(request, ex_id: int):
    exercise = get_object_or_404(models.Exercise_list, id=ex_id)
    exercise.delete()
    return {"success": True}

#Vector
@app.post("/vector", response=schemas.VectorSchema, tags=["vectors"],auth=AuthBearer())
def create_vector(request , data: schemas.VectorSchemaIn):
    vector = models.Vector.objects.create(creator_id=request.auth,**data.dict()) 
    try:
        vector.save()
    except:
        raise HttpError(422, "Введены неправильные данные!!!")
    return vector


@app.get('/vectors', response=List[schemas.VectorSchema], tags=["vectors"])
def get_vectors(request):
    vectors = models.Vector.objects.all()
    return vectors

@app.get('/vectors/school', response=List[schemas.VectorSchema], tags=["vectors"])
def get_vectors_by_school(request):
    vectors = models.Vector.objects.filter(creator_id__school_id=request.auth.school_id)
    for vector in vectors:
        vector.update_num_courses()
        vector.update_duration()
    return vectors

@app.get('/vectors/school/{school_name}', response=List[schemas.VectorSchema], tags=["vectors"],auth=None)
def get_vectors_by_school_name(request,school_name: str):
    vectors = models.Vector.objects.filter(creator_id__school_id__sub_domen__contains=school_name)
    for vector in vectors:
        vector.update_num_courses()
        vector.update_duration()
    return vectors


@app.get('/vector/{vector_id}', response=schemas.VectorSchema, tags=["vectors"])
def get_vector(request,vector_id:int):
    return get_object_or_404(models.Vector,id=vector_id)

@app.put("/vector/{vector_id}", tags=["vectors"])
def update_vector(request, vector_id: int, payload: schemas.VectorSchemaIn):
    vector = get_object_or_404(models.Vector, id=vector_id)
    for attr, value in payload.dict().items():
        if(value):
            setattr(vector, attr, value)
    vector.save()
    return {"success": True}

@app.delete("/vector/{vector_id}", tags=["vectors"])
def delete_vector(request, vector_id: int):
    vector = get_object_or_404(models.Vector, id=vector_id)
    vector.delete()
    return {"success": True}
#Homework
@app.post("/homework", response=schemas.HomeWorkSchema, tags=["homeworks"])
def create_homework(request , data: schemas.HomeWorkSchemaIn):
    homework = models.HomeWork.objects.create(student_id=request.auth) 
    homework.lesson_id = get_object_or_404(models.Lesson,id=data.lesson_id)
    homework.course_id = get_object_or_404(models.Course,id=data.course_id)
    homework.title = data.title
    homework.desc = data.desc
    # homework.title_en = data.title_en
    # homework.title_kk = data.title_kk
    # homework.title_ru = data.title_ru
    # homework.desc_en = data.desc_en
    # homework.desc_kk = data.desc_kk
    # homework.desc_ru = data.desc_ru
    try:
        homework.save()
    except:
        raise HttpError(422, "Введены неправильные данные!!!")
    return homework


@app.get('/homework', response=List[schemas.HomeWorkSchema], tags=["homeworks"])
def get_homeworks(request):
    homeworks = models.HomeWork.objects.all()
    return homeworks

@app.get('/homework/{homework_id}', response=schemas.HomeWorkSchema, tags=["homeworks"])
def get_homeworks_by_id(request,homework_id:int):
    return get_object_or_404(models.HomeWork,id=homework_id)

@app.put("/homework/{homework_id}", tags=["homeworks"])
def update_homework(request, homework_id: int, payload: schemas.HomeWorkSchemaIn):
    homework = get_object_or_404(models.HomeWork, id=homework_id)
    for attr, value in payload.dict().items():
        if(value):
            setattr(homework, attr, value)
    homework.save()
    return {"success": True}

@app.delete("/homework/{homework_id}", tags=["homeworks"])
def delete_homework(request, homework_id: int):
    homework = get_object_or_404(models.HomeWork, id=homework_id)
    homework.delete()
    return {"success": True}

#Course_User
@app.post("/access", response=schemas.Course_userSchema, tags=["accesses"],auth=AuthBearer())
def create_access(request , data: schemas.Course_userSchemaIn):
    '''
    Запрос для создании доступа к курсу нужен:\nx`
        course_id = айди курса, 
        student_id = айди студента, 
        end_date = дата окончания доступа
    '''
    print(data)
    student_id = data.student_id
    course_id = data.course_id
    if student_id is None or course_id is None:
        raise HttpError(404, "Введены неправильные данные!!!")
    student = models.User.objects.get(pk=student_id)
    course = models.Course.objects.get(pk=course_id)
    if student is None or course is None:
        raise HttpError(404, "Введены неправильные данные!!!")
    
    try:
        access = models.Course_user(course_id=course,student_id=student,end_date=data.end_date)
        access.save()
    except:
        raise HttpError(404, "Введены неправильные данные!!!")
    return access


@app.post("/self_access", response=schemas.Course_userSchema, tags=["accesses"])
def create_self_access(request , data: schemas.Course_userSchemaSelfIn):
    '''
    Запрос для создании доступа к курсу авторизованному пользователю нужен:\n
        course_id = айди курса, 
        end_date = дата окончания доступа
    '''
    access = models.Course_user.objects.create(course_id=models.Course.objects.filter(id=data.course_id).first(),student_id=request.auth,end_date=data.end_date)
    try:
        access.save()
    except:
        raise HttpError(422, "Введены неправильные данные!!!")
    return access


@app.get('/accesses', response=List[schemas.Course_userSchema], tags=["accesses"])
def get_accesses(request):
    '''
    Запрос для получении всех доступов к курсу.
    '''
    return models.Course_user.objects.all()

@app.get('/accesses/self', response=List[schemas.Course_userSchema], tags=["accesses"])
def get_self_accesses(request):
    '''
    Запрос для получении всех доступов к курсу.
    '''
    return models.Course_user.objects.filter(student_id=request.auth)

@app.get('/accesses/{student_id}', response=List[schemas.Course_userSchema], tags=["accesses"])
def get_student_accesses(request,student_id:int):
    '''
    Запрос для получении всех доступов к курсу.
    '''
    student = models.User.objects.get(pk=student_id)
    return models.Course_user.objects.filter(student_id=student)

@app.get('/access/{access_id}', response=schemas.Course_userSchema, tags=["accesses"])
def get_access(request,access_id:int):
    '''
    Запрос для получении определеного доступа к курсу по айди.
    '''
    return get_object_or_404(models.Course_user,id=access_id)


@app.put("/access/{access_id}", tags=["accesses"])
def update_access(request, access_id: int, payload: schemas.Course_userSchemaIn):
    '''
    Запрос для обновление определеного доступа к курсу по айди.
    '''
    access = get_object_or_404(models.Course_user, id=access_id)
    for attr, value in payload.dict().items():
        if(value):
            if(attr=="course_id"):
                access.course_id=models.Course.objects.filter(id=value).first()
            elif(attr=="student_id"):
                access.student_id=models.User.objects.filter(id=value).first()
            else:
                setattr(access, attr, value)
    access.save()
    return {"success": True}

@app.delete("/access/{access_id}", tags=["accesses"])
def delete_access(request, access_id: int):
    '''
    Запрос для обновление определеного доступа к курсу по айди.
    '''
    access = get_object_or_404(models.Course_user, id=access_id)
    access.delete()
    return {"success": True}


#Group
@app.post("/group", response=schemas.GroupSchema, tags=["groups"])
def create_group(request , data: schemas.GroupSchemaIn):
    group = models.Group.objects.create(teacher_id=data.teacher_id) 
    try:
        for i in data.course_id:
            group.course_id.add(get_object_or_404(models.Course,id=i.id))
        group.save()
    except:
        raise HttpError(422, "Введены неправильные данные!!!")
    return group

@app.put("/group/{group_id}", tags=["groups"])
def update_group(request, group_id: int, payload: schemas.GroupSchemaIn):
    group = get_object_or_404(models.Group, id=group_id)
    for attr, value in payload.dict().items():
        if(value):
            if(attr=="course_id"):
                group.course_id.clear()
                for i in value:
                    group.course_id.add(get_object_or_404(models.Course,id=i.get('id')))
            elif(attr=="teacher_id"):
                if(value):
                    group.teacher_id=(get_object_or_404(models.User,id=value.get('id')))
    group.save()
    return {"success": True}


@app.get('/groups', response=List[schemas.GroupSchema], tags=["groups"])
def get_groups(request):

    return models.Group.objects.all()

@app.get('/groups/{group_id}', response=schemas.GroupSchema, tags=["groups"])
def get_group(request,group_id:int):
    return get_object_or_404(models.Group,id=group_id)

@app.get('/groups/course/{course_id}', response=List[schemas.GroupSchema],auth=None, tags=["groups"])
def get_group_by_course(request,course_id:int):
    return models.Group.objects.filter(course_id=course_id)


@app.delete("/group/{group_id}", tags=["groups"])
def delete_group(request, group_id: int):
    group = get_object_or_404(models.Group, id=group_id)
    group.delete()
    return {"success": True}

#Roles
@app.post("/role", response=schemas.RoleSchema, tags=["roles"],auth=AuthBearer())
def create_role(request , data: schemas.RoleSchemaIn):
    try:
        role = Role.objects.create(school_id=request.auth.school_id,name=data.name,description=data.description) 
        for i in data.permissions:
            print(i)
            role.permissions.add(Permission.objects.filter(id=i.id).first())
    except:
        raise HttpError(422, "Введены неправильные данные или уже Роль с таким названием уже существует!")
    return role


@app.get('/roles', response=List[schemas.RoleSchema], tags=["roles"])
def get_roles(request):
    return Role.objects.all()

@app.get('/role/{role_id}', response=schemas.RoleSchema, tags=["roles"])
def get_role(request,role_id:int):
    return get_object_or_404(Role,id=role_id)

@app.put("/role/{role_id}", tags=["roles"])
def update_role(request, role_id: int, payload: schemas.RoleSchemaIn):
    role = get_object_or_404(Role, id=role_id)
    for attr, value in payload.dict().items():
        if(value):
            if(attr=="school_id"):
                role.school_id=models.School.objects.filter(id=request.auth.school_id.id).first()
            elif(attr=="permissions"):
                role.permissions.clear()
                for i in value:
                    role.permissions.add(Permission.objects.filter(id=i.get('id')).first())
            else:
                setattr(role, attr, value)
    role.save()
    return {"success": True}

@app.delete("/role/{role_id}", tags=["roles"],auth=AuthBearer())
def delete_role(request, role_id: int):
    role = get_object_or_404(Role, id=role_id)
    if(request.auth.school_id==role.school_id):
        role.delete()
        return {"success": True}
    return {"success":False}

#Perm
@app.get('/permission/{permission_id}', response=schemas.PermissionSchema, tags=["permissions"])
def get_permission(request,permission_id:int):
    return get_object_or_404(Permission,id=permission_id)

#Ticket
@app.post("/ticket", response=schemas.TicketSchema, tags=["tickets"])
def create_ticket(request , data: schemas.TicketSchemaIn):
    try:
        ticket = models.Ticket.objects.create(**data.dict())
        ticket.sender = request.auth
        ticket.save()
    except:
        raise HttpError(422, "Введены неправильные данные или уже Роль с таким названием уже существует!")
    return ticket


@app.get('/tickets', response=List[schemas.TicketSchema], tags=["tickets"])
def get_roles(request):
    return models.Ticket.objects.all()

@app.get('/ticket/{ticket_id}', response=schemas.TicketSchema, tags=["tickets"])
def get_ticket(request,ticket_id:int):
    return get_object_or_404(models.Ticket,id=ticket_id)

@app.put("/ticket/{ticket_id}", tags=["tickets"])
def update_role(request, ticket_id: int, payload: schemas.TicketSchemaIn):
    ticket = get_object_or_404(models.Ticket, id=ticket_id)
    for attr, value in payload.dict().items():
        if(value):
            setattr(ticket, attr, value)
    ticket.save()
    return {"success": True}

@app.delete("/ticket/{ticket_id}", tags=["tickets"])
def delete_role(request, ticket_id: int):
    ticket = get_object_or_404(models.Ticket, id=ticket_id)
    if(request.auth==ticket.sender):
        ticket.delete()
        return {"success": True}
    return {"success":True}

#Payment
@app.post("/payment", response=schemas.PaymentSchema, tags=["payments"])
def create_payment(request, data: schemas.PaymentSchemaIn):
    try:
        payment = models.Payment.objects.create(
        	payment_id=data.payment_id,
        	status=data.status,
        	price_ru=data.price_ru,
        	price_kk=data.price_kk,
        	price_en=data.price_en,
        	course_id=get_object_or_404(models.Course,id=data.course_id))
        payment.user = request.auth
        payment.save()
       

    except:
        raise HttpError(422, "Введены неправильные данные!")
    return payment


@app.post("/payment_for_user/{user_id}", response=schemas.PaymentSchema, tags=["payments"])
def create_payment_for_user(request, data: schemas.PaymentSchemaIn, user_id: int):
    user_course = get_object_or_404(models.Course, id=data.course_id)
    user_ = get_object_or_404(models.User, id=user_id)
    if models.Payment.objects.filter(course_id=user_course, user=user_).exists()==True:
        raise HttpError(422, "уже существует")
    else:
        try:
            payment = models.Payment.objects.create(
                payment_id=data.payment_id,
                status=data.status,
                price_ru=data.price_ru,
                price_kk=data.price_kk,
                price_en=data.price_en,
                course_id=get_object_or_404(models.Course,id=data.course_id))
            payment.user = get_object_or_404(models.User,id=user_id)
            payment.save()

        except:
            raise HttpError(422, "Введены неправильные данные!")
    return payment


@app.get('/payments', response=List[schemas.PaymentSchema], tags=["payments"])
def get_payments(request):
    return models.Payment.objects.all()

@app.get('/payment/{payment_id}', response=schemas.PaymentSchema, tags=["payments"])
def get_payment(request,payment_id:int):
    return get_object_or_404(models.Payment,id=payment_id)

@app.put("/payment/{payment_id}", tags=["payments"])
def update_payment(request, payment_id: int, payload: schemas.PaymentSchemaIn):
    payment = get_object_or_404(models.Payment, id=payment_id)
    for attr, value in payload.dict().items():
        if(value):
            setattr(payment, attr, value)
    payment.save()
    return {"success": True}



@app.delete("/payment/{payment_id}", tags=["payments"])
def delete_payment(request, payment_id : int):
    payment = get_object_or_404(models.Payment, pk=payment_id)
    course_id = payment.course_id
    user_id = payment.user_id
    try:
        course_for_user = models.Course_user.objects.get(student_id=user_id, course_id=course_id)
        course_for_user.delete()
    except:
        pass
    payment.delete()
    return {"success": True}


@app.get("/payments/paid/{user_id}",response=List[schemas.PaymentSchemaForUser], tags=['payments'])
def payment_user(request, user_id:int):
    user = models.Payment.objects.filter(user=user_id)
    return user

