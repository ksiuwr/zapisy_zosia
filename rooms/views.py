# -*- coding: UTF-8 -*-

from django.views.decorators.cache import cache_page
from django.http import *
from django.template import Context
from django.template.loader import get_template
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
import random
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from models import *
from datetime import *
from common.helpers import *

# from models import *

@login_required
def index(request):
    """

    """
    if not request.user.has_opened_records:
        raise Http404

    user = request.user
    title = "Rooms"
    return render_to_response('rooms.html',locals())


#@login_required
@cache_page(30)
@csrf_exempt
def json_rooms_list(request):
    if not request.user.has_opened_records:
        raise Http404
    json = Room.objects.to_json(request)
    return HttpResponse(json, mimetype="application/json")

def dict_to_json(d):
    ret = []
    for k,v in d.items(): ret.append('"%s":"%s"'%(k,v))
    return '{%s}'%(','.join(ret))


def get_in_room(usr,room,own=False):
    occupation = UserInRoom( locator=usr,
                             room=room,
                             ownership=own
                           )
    occupation.save()

def get_room_locators(room):
    # return html
    occs = UserInRoom.objects.filter(room=room)
    if not occs:
        return ''
    else:
        lst =  ','.join( [ u" %s"%o.locator for o in occs ] )
        return u"Mieszkają tu: %s<br/>" % lst

@login_required
def trytogetin_room(request):
    if not request.POST: raise Http404
    if not has_user_opened_records(request.user): return HttpResponse('fail')
    room = Room.objects.filter(hidden=False).get(id=int(request.POST['rid']))
    if room.password == request.POST['key']:
        get_in_room(request.user, room)
        return HttpResponse('ok')
    return HttpResponse('fail')

@login_required
@csrf_exempt
def open_room(request):
    if not request.POST: raise Http404
    if not has_user_opened_records(request.user): return HttpResponse('fail')
    occupation = UserInRoom.objects.get(locator=request.user)
    if occupation.ownership:
        room = occupation.room
        if room.password == request.POST['key']:
            occupation.room.short_unlock_time = datetime.now()
            occupation.room.save()
            return HttpResponse('ok')

@login_required
@csrf_exempt
def close_room(request):
    if not request.POST: raise Http404
    if not has_user_opened_records(request.user): return HttpResponse('fail')
    occupation = UserInRoom.objects.get(locator=request.user)
    if occupation.ownership:
        room = occupation.room
        no_locators = 0
        if room.password == request.POST['key']:
            no_locators = UserInRoom.objects.filter(room=room).count()
        if no_locators == 1: # user is still alone in this room
                timeout = timedelta(0,4*60*60,0)
                occupation.room.short_unlock_time = datetime.now() + timeout
                occupation.room.save()
                return HttpResponse('ok')


CONST_LEAVE_ROOM_BTN = u'<button onclick=\'window.location=/leave_room/\'>Opuść pokój</button>'
CONST_OK_BTN = u'<button onclick=\'hideDialog()\'>OK</button>'
CONST_OK2_BTN = u'<button onclick=\'hideDialog()\'>Zostań w pokoju</button>'
# CONST_LEAVE_OPEN_ROOM_BTN = u'<button onclick=\'Rooms.hideDialog(1)\'>Otwórz pokój</button>'
# CONST_USE_KEY_BTN = u'<button>Zamknij pokój</button>'
def leave_open_room_btn(key): return u'<button onclick=\'Rooms.hideDialog(%s)\'>Wejdź i nie zamykaj</button>' % key
def close_room_btn(key): return u'<button onclick=\'Rooms.closeRoom(%s)\'>Wejdź i zamknij kluczem</button>' % key
CONST_FORM = u"""<form><input type=\'submit\' value=\'Ustaw hasło\'/></form>"""


@login_required
@csrf_exempt
def leave_room(request):
    try:
        prev_occupation = UserInRoom.objects.get(locator=request.user)
        prev_occupation.delete()
    except Exception: pass
    # finally: TODO check which versions of Python support 'finally' keyword
    return HttpResponseRedirect('/rooms/')


@require_POST
@login_required
@csrf_exempt
def modify_room(request):
    # get correct room based on rid
    room_number = request.POST['rid'][1:]
    room = Room.objects.filter(hidden=False).get(number=room_number)
    status = room.get_status(request)
    json = { "room_number":room_number, "buttons":'', 'msg':'', 'form':'' }
    prev_occupation = None
    try:
        prev_occupation = UserInRoom.objects.get(locator=request.user)
    except Exception:
        pass
    if not status:
        #
        # this room is open
        #
        msg = ''
        no_locators = room.get_no_locators()
        if not no_locators:
            #
            # case when room is empty
            #
            if prev_occupation:
                json['msg'] = u"<br/>Jeśli chcesz się dopisać do tego pokoju,<br/>musisz najpierw wypisać się z pokoju %s.<br/>" % prev_occupation.room
                json['buttons'] = CONST_OK_BTN
            else:
                get_in_room(request.user, room, True)
                timeout = timedelta(0,120,0) # 2 minutes
                room.short_unlock_time = datetime.now() + timeout
                room.password = ''.join([ str(random.choice(range(10))) for _ in range(6) ])
                room.save()
                json['msg'] = u"<br/>Przekaż klucz swoim znajomym, aby<br/>mogli dołączyć do tego pokoju.<br/><br/>"
                json['form'] = u"Klucz do pokoju: <strong>%s</strong><br/>" % room.password
                json['buttons'] = close_room_btn(room.password) + leave_open_room_btn(room.password) + CONST_LEAVE_ROOM_BTN
        else:
            #
            # case when room is not empty
            #
            if (prev_occupation is not None) and (prev_occupation.room == room):
                json['msg'] = 'Mieszkasz w tym pokoju.'
                json['buttons'] = CONST_OK_BTN + CONST_LEAVE_ROOM_BTN
            elif (prev_occupation is None):
                get_in_room(request.user, room)
                json['msg'] = u"<br/>Właśnie dołączyłeś do tego pokoju<br/>"
                json['buttons'] = CONST_OK2_BTN + CONST_LEAVE_ROOM_BTN
            else: # prev_occ and not in this room
                json['msg'] = u"<br/>Jeśli chcesz się dopisać do tego pokoju,<br/>musisz najpierw opuścić pokój %s.<br/>" % prev_occupation.room
                json['buttons'] = CONST_OK_BTN
    elif status == 1:
        #
        # this room is locked or has password
        #
        if prev_occupation and (prev_occupation.room == room):
            json['msg'] = u"<br/>Zamknięty kluczem: <strong>%s</strong><br/>" % room.password
            json['buttons'] = CONST_OK_BTN + CONST_LEAVE_ROOM_BTN
        elif not prev_occupation:
            json['msg'] = u"<br/>Ten pokój jest zamknięty.<br/><input id='in_key' type='text' maxlength='6' size='6'></input><button onclick=\'Rooms.tryGetIn(%s)\'>Dopisz się</button>" % room.id
            json['buttons'] = u"<button onclick=\'hideDialog()\'>Anuluj</button>"
        else: # prev_occ and not in this room
            json['msg'] = u"<br/>Ten pokój jest zamknięty kluczem. Ponadto jeśli chcesz się do niego dopisać musisz najpierw opuścić pokój %s.<br/>" % prev_occupation.room
            json['buttons'] = CONST_OK_BTN
    elif status == 2: # room is full
        #
        # TODO: opcja do wypisania sie?
        #
        json['msg'] = u"<br/>Ten pokój jest już pełny.<br/>"
        json['buttons'] = CONST_OK_BTN
        if prev_occupation and (prev_occupation.room == room):
            json['buttons'] = CONST_OK_BTN + CONST_LEAVE_ROOM_BTN

    elif status == 3:
        json['msg'] = u"<br/>Zapisy na pokoje są zamknięte.<br/>"
        json['buttons'] = CONST_OK_BTN
    json['locators'] = get_room_locators(room)
    return HttpResponse(dict_to_json(json), mimetype="application/json")

