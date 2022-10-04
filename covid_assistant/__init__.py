# -*- coding: utf-8 -*-
"""This module contains a MindMeld application"""
from mindmeld import Application
from mindmeld.components.dialogue import AutoEntityFilling
from mindmeld.core import FormEntity
from mindmeld.components.nlp import NaturalLanguageProcessor

import json
import os

nlp = NaturalLanguageProcessor(app_path='covid_assistant')
nlp.build(incremental=True)
app = Application(__name__)

__all__ = ["app"]

# User data class and helper functions for handlers

user = None


class User:
    def __init__(self, request):
        self.sample_users = {
            "johndoe123": 0,
            "larry_l12": 1,
            "splashbro30": 2,
        }
        user = self._pull_data(request)
        directory = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(directory, "data/sample_user_data.json")
        with open(path) as f:
            data = json.load(f)
            self.data = data[user]

    def _pull_data(self, request):
        return False


@app.handle(domain='greeting', intent='greet')
def greet(request, responder):
    """
    When the user asks an unrelated question, convey the lack of understanding for the requested
    information and prompt to return to food ordering.
    """
    try:
        # Get user's name from session information in a request to personalize the greeting.
        responder.slots['name'] = request.context['name']
        prefix = 'Hello {name}. '
    except KeyError:
        prefix = 'Hello. '

    # responder.params.allowed_intents = ['greet']
    replies = ["Welcome to the covid assistant chatbot, here are some suggestion of want you can do with this "
               "application"]
    responder.reply(replies)


@app.handle(domain='greeting', intent='exit')
def exit(request, responder):
    """
    When the user asks an unrelated question, convey the lack of understanding for the requested
    information and prompt to return to food ordering.
    """

    replies = [
        "Have a nice day, and thanks for using our application"]
    responder.reply(replies)


@app.handle(intent='cancel')
def cancel(request, responder):
    """
    When the user asks an unrelated question, convey the lack of understanding for the requested
    information and prompt to return to food ordering.
    """

    replies = [
        "Okay, I will cancel your previous booking"]
    responder.reply(replies)


# TODO:FORM for covid booking
form_book_ppv_appointment = {
    'entities': [
        FormEntity(
            entity='name',
            responses=['Sure. What is your full name?'],
            retry_response=["Please provide us full name as per your IC."],
        ),
        FormEntity(
            entity='ic_number',
            responses=['What is your IC number?'],
            value=
            {
                "ic_number": "ic"
            }
            ,
            retry_response=["Please provide valid identification number."],
        ),
        FormEntity(
            entity='phone_number',
            responses=['What is your phone number?'],
            retry_response=["Please use the appropriate format for phone number"],
        ),
        FormEntity(
            entity='email_address',
            responses=['What is your email address?'],
            retry_response=["Email address provided does not exist"],
        ),
        FormEntity(
            entity='state',
            responses=['Which state do you live in'],
            retry_response=["Please provide state that are in Malaysia"],
        ),
        FormEntity(
            entity='city',
            responses=['What city do you reside in?'],
            retry_response=["Please provide city that are in Malaysia"],
        ),
        FormEntity(
            entity='pp_centre_choice',
            responses=['Great, at which PPV centre would you like to take the vaccine?',
                       'BP SPECIALIST CENTRE (MEGAH)',
                       'KELINIK LOH',
                       'KLINIK FAMILI TTDI SDN BHD',
                       'KLINIK ALAM MEDIC',
                       'KLINIK AMCEN',
                       ],
            # TODO need to give option to user
            retry_response=["The selected PPV centre is not available in your selected location"],
        )
    ],
    'max_retries': 2,
    'exit_keys': ['cancel',
                  'quit',
                  'exit',
                  'i want to cancel'
                  ],
    'exit_msg': "Okay, I have cancelled your booking for the vaccination appointment."
}


@app.auto_fill(intent='booking', form=form_book_ppv_appointment)
def booking(request, responder):
    """
    When the user asks an unrelated question, convey the lack of understanding for the requested
    information and prompt to return to food ordering.
    """

    text_file = open(r"D:\Discoverix\Discoverix-Krispi\Krispy\mind_meld_0.1\covid_assistant\save_dummy.txt", "a")

    for entity_obj in request.entities:
        responder.slots['name'] = entity_obj['value']
        responder.slots['ic_number'] = entity_obj['value']
        responder.slots['phone_number'] = entity_obj['value']
        responder.slots['email_address'] = entity_obj['value']
        ## TODO check why value is empty, if slot is working properly // if not python object

    user = User(request)  # fetch user information
    responder.frame['user'] = user
    AutoEntityFilling(handler=check_booking_status_followup_handler, form=form_book_ppv_appointment, app=app).invoke(
        request, responder)

    replies = [
        "Okay, I will help you out! Please give us some time to process your details"]
    responder.reply(replies)


@app.dialogue_flow(domain='general_faq', intent='symptoms_check')
def check_symptoms(request, responder):
    """
    When the user asks an unrelated question, convey the lack of understanding for the requested
    information and prompt to return to food ordering.
    """
    responder.frame['count'] = responder.frame.get('count', 0) + 1
    # domains = request.history

    if responder.frame['count'] <= 3:
        replies = [
            f"Here are the following information regarding COVID-19 symptoms"]
        responder.reply(replies)
    else:
        responder.reply('Sorry I cannot help you. Please try again with another commands.')
        responder.exit_flow()


@app.handle(intent='covid_definition')
def covid_meaning(request, responder):
    """
        Trigger when user asks the definition of covid-19
    """
    responder.reply("COVID is a respiratory disease that have similarity with SARS and infect people rapidly")


@app.handle(domain='ppv_centre', intent='check_status')
def check_booking_status(request, responder):
    """
    To be triggered when the user wants to check their booking status, should be able to retrieve the past slot
    made on the booking form based on the information checked
    """
    user = User(request)  # fetch user information
    responder.frame['user'] = user
    AutoEntityFilling(handler=check_booking_status_followup_handler, app=app).invoke(request, responder)


def check_booking_status_followup_handler(request, responder):
    """
    To be triggered when the user wants to check their booking status, should be able to retrieve the past slot
    made on the booking form
    """
    for entity in request.entities:
        # print(entity)
        if entity['type'] == 'ic_number':
            responder.slots['text'] = entity['text']

    responder.reply('Checking your status for your booking with the ic {ic_number}')
    responder.exit_flow()


# TODO change the name of this fucntion, make sure its linked or flows to the function below
@app.dialogue_flow(intent='check_place_available')
def check_place_availability(request, responder):
    ppv_place_list = ['BP SPECIALIST CENTRE (MEGAH)',
                      'KELINIK LOH',
                      'KLINIK FAMILI TTDI SDN BHD',
                      'KLINIK ALAM MEDIC'
                      ]
    responder.params.dynamic_resource['gazetteers'] = {'ppv_centre': dict((ppv_centre, 1.0) for
                                                                          ppv_centre in ppv_place_list)}
    prompt = "I found the place at " + ','.join(ppv_place_list) + '.where do you want to take the vaccine?'
    responder.reply(prompt)


@app.dialogue_flow()
def give_place_option(request, responder):
    active_ppv_centre = None
    ppv_centre_entity = next((e for e in request.entities if e['type'] == 'ppv_centre'), None)
    print(f"----> store entity {request.entities}")
    if ppv_centre_entity:
        print(" -------> PPV centre entity function")
        try:
            vaccine_centre = app.question_answerer.get(index='ppv_centre', id=ppv_centre_entity['value']['id'])
        except TypeError:
            vaccine_centre = app.question_answerer.get(index='ppv_centre', id=ppv_centre_entity['text'])
        try:
            active_ppv_centre = vaccine_centre[0]
            responder.frame['target_ppv_centre'] = active_ppv_centre
        except IndexError:
            responder.reply('No PPV centre open at time of the request')
    elif 'target_ppv_centre' in responder.frame:
        active_ppv_centre = responder.frame['target_ppv_centre']

    if active_ppv_centre:
        responder.slots['ppv_centre_name'] = active_ppv_centre['ppv_centre_name']
        responder.reply('The {ppv_centre_name} is available')

    responder.frame['count'] = responder.frame.get('count', 0) + 1

    if responder.frame['count'] <= 3:
        responder.reply('Which vaccine centre would you like to know about?')
        responder.listen()

    else:
        responder.reply('Sorry I cannot help you. Please try again')
        responder.exit_flow()


# TODO : Give selectable actions for the list of PPV displayed above
@app.dialogue_flow(intent='show_available_action')
def available_action(request, responder):
    available_action_list = [
        'Book Vaccine',
        'Schedule RTK test',
        'See operation hour'
    ]

    responder.params.dynamic_resource['gazetteers'] = {' ': dict((actions, 1.0) for
                                                                 actions in available_action_list)}
    prompt = "Here are some suggestions of action you can do. " + ','.join(available_action_list) + \
             '. Have anything in particular to do?'

    responder.reply(prompt)


# TODO this function should be able to grab the choosen activity above and display unique query
@app.dialogue_flow(intent='')
def available_action_followup(request, responder):
    choice_activity_1 = None
    choice_activity_2 = None
    choice_activity_3 = None

    if choice_activity_1:
        pass
    if choice_activity_2:
        pass
    if choice_activity_3:
        pass


@check_place_availability.handle(default=True)
def default_handler(request, responder):

    responder.frame['count'] = responder.frame.get('count', 0) + 1

    if responder.frame['count'] <= 3:
        responder.reply('Sorry, I could not get you, Which vaccine centre would you like to know about?')
        responder.listen()
    else:
        responder.reply('Sorry I cannot help you. Please try again.')
        responder.exit_flow()


@check_place_availability.handle(intent="check_available_place")
def check_place_availability_in_flow_handler(request, responder):
    check_place_availability(request, responder)


@app.handle(domain='unsupported', intent='unsupported')
def unsupported(request, responder):
    """
        This functions handles unsupported query, and give user suggestion on what to ask instead
    """
    responder.reply("Sorry your query is not available, please ask question relating to COVID-19.")


@app.middleware
def incoming_message_middleware(request, responder, handler):
    """
        This function should trigger when user gives out command that is not available in the intent recognizer
    """
    handler(request, responder)
    # try:
    #     handler(request,responder)
    # except Exception as ex:
    #
    #     responder.directives = []
    #     responder.reply("The requests sent is unsuccessful, try another command")
