from openai import OpenAI
import json
import re
import os
from gtts import gTTS
import app

screenplay = """
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
"""

# Strip the screenplay tags to get plain text
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
    

# Cleaned screenplay text
cleaned_text = clean_screenplay_text(screenplay,app.config['API_KEY'])
def convert_text_to_speech2(text, output_file):
    tts = gTTS(text, lang='en')
    tts.save(output_file)
    print(f"Speech saved as: {output_file}")

# def convert_text_to_speech(text, output_file):
#     engine = pyttsx3.init()
#     engine.save_to_file(text, output_file)
#     engine.runAndWait()
convert_text_to_speech2(cleaned_text, "C:/Users/Acer/Desktop/screenplay_audio3.mp3")


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
            temperature=0.1,
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



content = '''Liam stood on the edge of the cliff, staring at the vast ocean below. The wind whipped through his hair, but he didn’t flinch. His mind raced with memories of everything that had led him here. Footsteps approached behind him, and he didn’t have to turn to know it was Ava.

“You don't have to do this,” she said, her voice trembling.

He sighed, still gazing at the horizon. “It's too late.”

“It's never too late,” she insisted, taking a step closer. “Please, Liam, come back with me.”

Silence hung in the air as he weighed her words.

'''

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
            max_tokens=100
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

play = '''<heading>INT. VAN - DAY</heading>
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
'''

print(os.environ.get("API_KEY"))