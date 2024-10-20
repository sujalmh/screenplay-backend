from flask import request, jsonify
from openai import OpenAI
import json
import re
import os
from gtts import gTTS
from models import db, Conversation

def clean_screenplay_text(screenplay,api_key):
    client = OpenAI(
        api_key= api_key
    )
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Convert the given screenplay text into a narration instance which can be used for text to speech."},
                {"role": "user", "content": screenplay}
            ],
            model ="gpt-4o",
            temperature= 0.1,
            max_tokens= 100
        )
        response = chat_completion.choices[0].message.content.strip()
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None
    

def convert_text_to_speech2(text, output_file):
    tts = gTTS(text, lang='en')
    tts.save(output_file)
    print(f"Speech saved as: {output_file}")



def rate_screenplay(screenplay_content, api_key):
    client = OpenAI(
        api_key= api_key
    )

    system_prompt = f"""You are a professional screenwriter and a screenplay critic. Your response should be based on the following:
                    Plot, Character Development, Dialogue, Originality, and Theme. Rate each criterion out of 10 in the format:
                    Plot: [score]
                    Character Development: [score]
                    Dialogue: [score]
                    Originality: [score]
                    Theme: [score]
                    The given screenplay will have custom tags for:
                    Scene headings, Action lines, Characters, Dialogue, Parenthesis.
                    Understand each tag and rate correctly.
                """
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": screenplay_content}
            ],
            model="gpt-4", 
            temperature=0.5,
            max_tokens=100
        )

        response = chat_completion.choices[0].message.content.strip()

        scores = {}
        criteria = ["Plot", "Character Development", "Dialogue", "Originality", "Theme"]
        for criterion in criteria:
            match = re.search(rf"{criterion}:\s*(\d+)", response)
            if match:
                scores[criterion] = int(match.group(1))
            else:
                scores[criterion] = None

        return json.dumps(scores)
        
    except Exception as e:
        print(f"Could not generate analysis: {e}")
        return None

def convert_to_screenplay(screenplay_content, api_key):
    client = OpenAI(
        api_key= api_key
    )
    system_prompt = """Format the following text into screenplay format:
    
    Use the following format:
    - <heading> for scene heading
    - <sub-heading> for scene subheading
    - <action> for action descriptions
    - <character> for character names
    - <parenthesis> for parentheticals (like voiceovers, actions)
    - <dialogue> for dialogue
    - <shot> for shot
    Ensure each tag has both an opening and a closing tag.
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": """
Adejo still wasn't quite sure how his uncle had got caught up with the two wedding guests in the first place.
He had never been to a wedding before and had been excited until his uncle made it clear that they weren't really going to the wedding. 
'We're just going to the kitchen, to pick up the bags. We won't even see the wedding. I'm sorry Adejo. You'll hear it though. I can promise you that.' 
For a while it seemed that they wouldn't even hear the wedding, let alone see it, because when his uncle parked the van and went to the steel door that led to the kitchen it wouldn't open, no matter how many times his uncle tried pressing different numbers into the pad on the wall.
"""},           
                {"role": "assistant", "content": """
<heading>INT. VAN - DAY</heading>
<sub-heading>INSIDE THE VAN</sub-heading>
<shot>Camera zooms in on Adejo's face.</shot>
<action>Adejo, a young boy, looks confused. His Uncle, a middle-aged man, is at the wheel.</action>
<character>ADEJO</character>
<parenthesis>(voiceover)</parenthesis>
<dialogue>I still wasn't quite sure how my uncle had got caught up with the two wedding guests in the first place.</dialogue>
<action>Adejo's Uncle turns to him, a serious look on his face.</action>
<character>UNCLE</character>
<dialogue>We're just going to the kitchen, to pick up the bags. We won't even see the wedding.</dialogue>
<action>The van pulls up to a steel door. His uncle starts pressing numbers into the keypad, but the door won't open.</action>
"""},
                {"role": "user", "content": screenplay_content}
            ],
            model="gpt-4o", 
            temperature=0.1,
            max_tokens=1000
        )
        output = {
            "screenplay": screenplay_content,
            "analysis": chat_completion.choices[0].message.content.strip()
        }
        return output["analysis"]
        
    except Exception as e:
        print(f"Could not generate analysis: {e}")
        return None

def summarize_screenplay(screenplay_content,api_key):
    client = OpenAI(
        api_key= api_key
    )

    system_prompt = f"""You are a professional screenwriter and a screenplay critic. Summarize the given screenplay."""
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": screenplay_content}
            ],
            model="gpt-4", 
            temperature=0.3,
            max_tokens=100
        )

        response = chat_completion.choices[0].message.content.strip()
        return json.dumps(response)
        
    except Exception as e:
        print(f"Could not generate analysis: {e}")
        return None

def get_sentimental_analysis(screenplay, api_key):
    if not screenplay:
        return
    else:
    
        client = OpenAI(
            api_key = api_key
        )
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": """ You are a screenplay professional. Analyze the given scene and
                                                        provide an emotional analysis of the scene. I want the emotional
                                                        analysis to be 1-3 Emojis that potray those emotions and then a brief 2-3 line text. Strictly use face emojis do not use objects. The
                                                        intensity of the emoji should be based on the emotion analysis.
                                                        Let it be in JSON format. Just start and end with flower brackets.
                                                    """},
                    {"role": "user", "content": "<action>Adejo's Uncle turns to him, an angry look on his face. His uncle looked at him confused</action>"},
                    { "role": "assistant", "content": '{"emojies": [{"name": "Angry face", "emoji": "\\U0001f620"},{"name": "Confused face", "emoji": "\\U0001f615"}], "description": "The scene is tense as uncle is angered by Adejo"}'},
                    {"role": "user", "content": screenplay}
                ],
                model ="gpt-4o",
                temperature= 0.5,
                max_tokens= 100
            )
            r = chat_completion.choices[0].message.content.strip()
            fixed_json_string = r.replace('\\', '\\\\')
            parsed_data = json.loads(fixed_json_string)
            scene_emoji = parsed_data['emojies']
            scene_description = parsed_data['description']
            return scene_emoji, scene_description
            
        except Exception as e:
            print({e})

def save_message(user_id,role, content):
    new_message = Conversation(user_id=user_id,role=role, content=content)
    db.session.add(new_message) 
    db.session.commit()

def get_conversation_history(user_id):
    conversations = Conversation.query.filter_by(user_id=user_id).all()
    return [{"role": convo.role, "content": convo.content} for convo in conversations]

def chatbot_chat(user_id, user_input,api_key):
    client = OpenAI(
        api_key= api_key
    )
    history= get_conversation_history(user_id)
    messages=  [{
                "role": "system", "content": """You are a professional screenplay writer and you will refer 
                                                to reputed and recognized sources on the internet for your answer.
                                                Use the user data provided to you and use previous conversation
                                                details for each user. Make sure to not deviate from the topic.
                                                Suggest,recommend,rate and help with the user with any queries related
                                                to screenplay,screenplay script writting """
                }]
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})
    try:
        chat_completion = client.chat.completions.create(
            messages= messages,
            model ="gpt-4o",
            temperature= 0.3,
            max_tokens= 1000 #Change this if required btw 
        )
        response = chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return jsonify({"error": "An error occurred while processing your request.", "details": str(e)}), 500
        
    save_message(user_id, "user",user_input)
    save_message(user_id,"assistant",response)
    return jsonify({"reply":response}),200

def generate_image(description, api_key):

  client =OpenAI(
          api_key= api_key)
  model = "dall-e-3"
  prompt = description

  response = client.images.generate(
    prompt=prompt,
    model=model,
    response_format="url"
  )
  return response.data[0].url.strip()

    
    
