from typing import Any, Text, Dict, List, Optional
from numpy import insert
from rasa_sdk import Tracker, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.events import SlotSet,FollowupAction, ActiveLoop, UserUtteranceReverted
from rasa_sdk.interfaces import EventType
from rasa_sdk.types import DomainDict
import pymysql as mysql

def clean_name(name):
    return "".join([c for c in name if c.isalpha()])

# write an action function to connect to local host with users = "root" using PYMYSQL
class ActionSaveToDB(Action):
    def name(self) -> Text:
        return "action_save_to_db"
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            mydb = mysql.connect(host="localhost",user="root",passwd="",database="rasa")
            print("connected to database")
            cur = mydb.cursor()
            insert_query = "INSERT INTO users (name, email, number) VALUES (%s, %s, %s)"
            data = (tracker.get_slot("first_name"), tracker.get_slot("email"), tracker.get_slot("number"))
            cur.execute(insert_query, data) 
            mydb.commit()
            mydb.close()        
            return []
        except Exception as e:
            print("Error while connecting to database", e)
            return []


# class ActionDefaultFallback(Action):
#     def name(self) -> Text:
#         return "action_default_fallback"
#     async def run(
#         self,
#         dispatcher: CollectingDispatcher,
#         tracker: Tracker,
#         domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#         dispatcher.utter_message(template="utter_default")
#         return [UserUtteranceReverted()]

    

class ActionRwoStageFallback(Action):
    def name(self) -> Text:
        return "action_two_stage_fallback"
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_ask_rephrase")
        return [UserUtteranceReverted()]    


class ActionCheckIfFirstNameIsKnown(Action):
    def name(self) -> Text:
        return "action_check_if_first_name_is_known"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        confirm_first_name = tracker.get_slot('confirm_first_name')

        if not confirm_first_name:
    # start the contact form
             return [FollowupAction("contact_form")]
        else: 
            # do nothing
            pass 

class ActionCheckConfirmFirstName(Action):

    def name(self) -> Text:
        return "action_check_confirm_first_name"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        confirm_first_name = tracker.get_slot('confirm_first_name')

        if confirm_first_name:
            # perform the action to confirm the first name
            dispatcher.utter_message(text=  f"Use this name {confirm_first_name}?")
        else:
            # do nothing
            pass

        return []       
        
class ActionSetFirstName(Action):

    def name(self) -> Text:
        return "action_set_first_name"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        confirm_first_name = tracker.get_slot('confirm_first_name')
        
        if confirm_first_name:
            # Perform the action to set the first name
            print('collecting',confirm_first_name)
            return [SlotSet("first_name", confirm_first_name), SlotSet("confirm_first_name", None),  
                    FollowupAction("contact_form")]
        else:
            pass    


class ValidateContactForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_contact_form"
    async def deactivate(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Okay, we have cancelled the form.")
        return await super().deactivate(dispatcher, tracker, domain)
    async def required_slots(
        self,
        slots_mapped_in_domain: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Optional[List[Text]]:
        return ["first_name", "email", "number"]
    # async def extract_first_name(
    #     self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    # ) -> Dict[Text, Any]:
    #     text_of_last_user_message = tracker.latest_message.get("text")
    #     intent = tracker.latest_message['intent'].get('name')
    #     if intent == "inform":
    #         return  {"first_name": None , "confirm_first_name": text_of_last_user_message}
    #     else:
    #         return {"first_name": None, "confirm_first_name": None}
    # async def validate_confirm_first_name(
    #     self,
    #     slot_value: Any,
    #     dispatcher: CollectingDispatcher,
    #     tracker: Tracker,
    #     domain: DomainDict,
    # ) -> Dict[Text, Any]:
    #     slot_value = clean_name(slot_value)
    #     if slot_value: 
    #             if slot_value  and len(slot_value) > 2 :       
    #                 dispatcher.utter_message(text=f"Use this name {slot_value}?")
    #                 return {"first_name": slot_value, "confirm_first_name": slot_value}
    #             else:
    #                 return {"first_name": None, "confirm_first_name": None}
    #     else:
    #         return {"first_name": None, "confirm_first_name": None}
            
    async def validate_first_name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        prev_mentioned_name = tracker.get_slot("confirm_first_name")
        prev_mentioned_name = clean_name(prev_mentioned_name) if prev_mentioned_name else None

        slot_value = clean_name(slot_value)
        if len(slot_value) < 3:
                dispatcher.utter_message(text="Your first_name should be at least 3 characters long.")
                return {"first_name": None, "confirm_first_name": None}
        if slot_value== prev_mentioned_name:
            return {"first_name": slot_value, "confirm_first_name": slot_value}
        
        # if the slot text contains "my name is" then extract the name
        phrases_to_eliminate = ["my name is", "I am"]

        for phrase in phrases_to_eliminate:
            if phrase in slot_value:
                slot_value = slot_value.split(phrase)[-1].strip()

        return {"first_name": slot_value, "confirm_first_name": None}
  
  
    
class ActionSubmit(Action):
    """
    This class is a custom action to submit the form.
    It is a subclass of the `Action` class provided by the Rasa SDK.

    Methods:
    - first_name: Returns the first_name of the action.
    - run: Submits the form. Retrieves the "utter_collect_info" response from the
           domain and formats it with the user's first_name and mobile number.
    """

    def name(self) -> Text:
        """Returns the first_name of the action."""
        return "action_submit"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """
        Submits the form. Retrieves the "utter_collect_info" response from the
        domain and formats it with the user's first_name and mobile number.

        Parameters:
        - dispatcher: the dispatcher which is used to send messages back to the user.
        - tracker: the state tracker for the current user.
        - domain: the bot's current domain.

        Returns:
        A list of events. In this case, it's an empty list because the form submission
        doesn't result in any events.
        """
        
       # response = domain["responses"]["utter_confirm_info"][0]
        first_name = tracker.get_slot("first_name")
        number = tracker.get_slot("number")
        email = tracker.get_slot("email")   
        response_text = f"We have collected the following information:  1. name {first_name}, 2 number {number}, 3 email is {email}."
        dispatcher.utter_message(text =response_text)
        return []
    

class ActionResetForm(Action):
        def name(self) -> Text:
            return "action_reset_form"

        async def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
        ) -> List[Dict[Text, Any]]:
            return [
                ActiveLoop(None),  # Deactivate the form
                SlotSet("first_name", None),  # Reset the 'first_name' slot
                SlotSet("email", None),  # Reset the 'email' slot
                SlotSet("number", None),  # Reset the 'number' slot
                SlotSet("confirm_first_name", None),  # Reset the 'confirm_first_name' slot
            ]
            
            