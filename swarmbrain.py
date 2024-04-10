import time
from datetime import datetime
from langchain.chat_models import AzureChatOpenAI
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)


def build_model(model_conf="", extra={}):
    return AzureChatOpenAI(
        **extra,
        openai_api_base="",
        openai_api_version="",
        model_version="",
        deployment_name="",
        openai_api_key="",
        openai_api_type="",
        temperature=0.5,
        # response_format={"type": "json_object"}
    )


model_gpt35_turbo = build_model()
model_gpt4 = build_model()
model_gpt4_32k = build_model()
model_gpt4_turbo = build_model()


def llm_gpt4(prompt: str, if_print_log: bool = False):
    return __llm_call(prompt, model_gpt4, if_print_log)


def llm_gpt4_32k(prompt: str, if_print_log: bool = False):
    return __llm_call(prompt, model_gpt4_32k, if_print_log)


def llm_gpt4_turbo(prompt: str, if_print_log: bool = False):
    return __llm_call(prompt, model_gpt4_turbo, if_print_log)


async def llm_gpt35_turbo(prompt: str, if_print_log: bool = False):
    return await __llm_call_async(prompt, model_gpt35_turbo, if_print_log)


def llm_gpt35_turbo2(prompt: str, if_print_log: bool = False):
    return __llm_call2(prompt, model_gpt35_turbo, if_print_log)


def __llm_call2(prompt: str, model, if_print_log: bool = False):
    print('\033[34m' + "executing GPT------------------" + '\033[0m')
    print(f"Model Name: {model.deployment_name}")
    print(f"Model Version: {model.model_version}")

    start_time = time.time()
    dt_object = datetime.fromtimestamp(start_time)

    formatted_time = dt_object.strftime('%Y-%m-%d %H:%M:%S')

    response = model.predict(prompt)

    end_time = time.time()

    input_count = len(prompt) / 4
    output_count = len(response) / 4

    return response


async def __llm_call_async(prompt: str, model, if_print_log: bool = False):
    print('\033[34m' + "executing GPT------------------" + '\033[0m')
    print(f"Model Name: {model.deployment_name}")
    print(f"Model Version: {model.model_version}")

    start_time = time.time()
    dt_object = datetime.fromtimestamp(start_time)

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(executor, model.predict, prompt)
    if if_print_log:
        print(response)

    end_time = time.time()

    input_count = len(prompt) / 4
    output_count = len(response) / 4

    return response


def __llm_call(prompt: str, model, if_print_log: bool = False):
    print('\033[34m' + "executing GPT------------------" + '\033[0m')
    print(f"Model Name: {model.deployment_name}")
    print(f"Model Version: {model.model_version}")

    start_time = time.time()
    dt_object = datetime.fromtimestamp(start_time)

    formatted_time = dt_object.strftime('%Y-%m-%d %H:%M:%S')

    response = model.predict(prompt)

    end_time = time.time()

    input_count = len(prompt) / 4
    output_count = len(response) / 4

    return response


def overmind_brain_initial():
    prompt = '''
You are an intelligent brain of Zerg swarm in StarCraft II game.
You are very aggressive and know all the dependencies between Zerg units, Zerg buildings, and Zerg technological research.

Your task is to analyze how many different Zerg units are needed at different stages of the game when facing powerful Terran players

---rule
The value given must be an exact value, for instance:
Zergling: 20
---

For instance:
RESPONSE FORMAT:

Early stage:
Zergling: [num]
Baneling: [num]
Roach: [num]
Ravager: [num]
Hydralisk: [num]
Infestor: [num]
Swarm host: [num]
Mutalisk: [num]
Corruptor: [num]
Viper: [num]
Ultralisk: [num]
Brood Lord: [num]

Mid stage:
Zergling: [num]
Baneling: [num]
Roach: [num]
Ravager: [num]
Hydralisk: [num]
Infestor: [num]
Swarm host: [num]
Mutalisk: [num]
Corruptor: [num]
Viper: [num]
Ultralisk: [num]
Brood Lord: [num]

Late stage:
Zergling: [num]
Baneling: [num]
Roach: [num]
Ravager: [num]
Hydralisk: [num]
Infestor: [num]
Swarm host: [num]
Mutalisk: [num]
Corruptor: [num]
Viper: [num]
Ultralisk: [num]
Brood Lord: [num]
    '''

    output1 = llm_gpt35_turbo2(prompt, True)

    return output1


def overmind_brain_initial2():
    prompt = '''
You are an intelligent brain of Zerg swarm in StarCraft II game.
You are very aggressive and know all the dependencies between Zerg units, Zerg buildings, and Zerg technological research.

Now, you need to answer the following questions:

Question 1: When the enemy's army launched an attack on your base, and you sent out all the attacking units, but the whole army was wiped out, you still have some Drones mining, will you send out all your Drones at this time to make the final resistance? If yes, answer True, otherwise answer False.

Question 2: When the enemy's army launched an attack on your base, you sent out all the attacking units, and all the enemy troops were defeated. At this time, you still have some attacking units. Will you send out your attacking units to counterattack the enemy's base? If yes, answer True, otherwise answer False.

RESPONSE FORMAT:
Question 1:
Question 2:
    '''

    output1 = llm_gpt35_turbo2(prompt, True)

    return output1


def overmind_brain_1():
    prompt = '''
You are an intelligent brain of Zerg swarm in StarCraft II game.
You are very aggressive and know all the dependencies between Zerg units, Zerg buildings, and Zerg technological research.
Your task is to generate construction commands for Zerg buildings.

You and Terran players are on a square map with 16 mines evenly distributed on the map, as shown in the following matrix:
[[0, B7, B6, B4, B2],
[A8, 0, B5, B3, B1],
[A1, A3, A5, 0, B8],
[A2, A4, A6, A7, 0]]
Currently, your base is at position A1 and the Terran base is at position B1. 0 represents no mine, and other letters represent the mine number.

---Current battle situation
game time: 00:00

The Units you currently have are: 12 Drone, 1 Overlord.
The Buildings you currently have are: 1 Hatchery

The Enemy Units you curently detect are: Nothing.
The Enemy Buildings you curently detect are: Nothing.

---

--- rule
You need to analyze the game progression by following a structured protocol based on the game situation. Make sure to include the following perspectives in your analysis:
1. Current Stage of the Match: Determine the current game stage based on the game time and types of our units, whether it’s early, middle, or late stage.
2. The Condition of Our Forces: Assess our current status in dimensions of:
2.1 Our Zerg Units and Buildings: Scrutinize the state of Zerg Units and Buildings.
2.2 Our Zerg Technology: Analyze the current status of the Zerg technological research based on the unlocked research.
3. Our current Zerg Operational Strategy: Devise a reasonable strategy based on our current situation, opponent’s situation, and scouting intel.
4. Opponent's situation: Assess opponent’s current status in dimensions of:
4.1 Opponent's Units and Buildings: Analyze state of opponent’s Units and Buildings.
4.1 Opponent's Tactical Plan and our Potential Risks: Based on detected opponent’s Units and Buildings, predict the opponent's attack timing to prepare defensive measures in advance.
5. Scouting Intel: Stress the importance of recent and consistent scouting reports to stay updated on the enemy's unit composition, positioning, and possible incoming attacks or expansions.
6. Eliminate Repeated instructions: Based on "Your commands in previous round", analysis which commands are not needed to execute again.
7. Avoid problematic commands: Analysis the problematic commands in "Avoid problematic commands", and avoid the problematic commands this time.
---

---Game Key Decisions Memory
The key decisions in your memory, you can refer to these decisions for strategic deployment.
{{
Based on previous competition experience, you found that:
0. Remember to build more hatchery to expend the economy, like (Drone, A1)->(Build)->(Hatchery, A1), (Drone, A1)->(Build)->(Hatchery, A2), (Drone, A1)->(Build)->(Hatchery, A3).
1. Remember to build Baneling Nest to enable morph Baneling to cause more damage.
2. You can morph many Zerglings to Banelings to cause more damage to the enemy's Marine, Marauder and Siege tanks.
3. You can morph many Roaches to Ravagers to cause more damage to the enemy's Marine, Marauder and Siege tanks.
4. At the early and mid stage of the game, a mixed army of Zergling, Baneling, Roach and Ravager can be unstoppable.
5. Remember to build the Infestation Pit to unlock the build of Lair.
6. Remember to build Hydralisk Den to unlock powerful Hydralisk to cause more damage.
7. Remember to build Ultralisk Cavern to unlock the powerful Ultralisk.
8. Remember to build Greater Spire to unlock the powerful Brood Lord.
}}
---

---Self-Verification (Avoid problematic commands)
These are the experiences you have gained through self-verification, please try to avoid these situations.
{{
'0': (Drone, A1)->(Expand Creep)->(A2)
Problem: Since "Drone" cannot expand creep (only Queens can), this instruction is unreasonable.
'1': (Drone, A1)->(Build)->(Queen Nest, A1)
Problem: This instruction is unreasonable. Drones cannot build Queen Nests; they are constructed by Drones transforming into the structure.
'2': (Drone, A1)->(Build)->(Overlord)
Problem: The problem is that "Drone" cannot hatch "Overlord", only "Larva" can hatch "Overlord".
'3': (Drone, A1)->(Build)->(Drone)
Problem: The problem is that "Drone" cannot hatch "Drone", only "Larva" can hatch "Drone".
}}
---

---Your commands in previous round
{{
    
}}
---

Based on the current battle situation and Units and Buildings from both sides, following the rules above, a brief step-by-step analysis can be done from our strategy, Units and Buildings, economic, technical perspectives, And "Your commands in last round".
Then, formulate 20 actionable, specific decisions (include the target location, like A1, A2, etc.) from the following action list.
These decisions should be numbered from 0, denoting the order in which they ought to be executed, with 0 signifying the most immediate and crucial action.

Note:
1. Game Key Decisions Memory is the key decisions in your memory, you can refer to these decisions for strategic deployment.
2. Self-Verification (Avoid problematic commands) is the experiences you have gained through self-verification, please try to avoid these situations.
3. Please reflect the 'Game Key Decisions Memory' and 'Self-Verification (Avoid problematic commands)' in the analysis of the results.
4. "Command Target" means the unit you want to command, such as "Drone", "Overlord", etc.
"Action" means the actions you want the unit to do, such as "Move", "Morph", etc.
"Target" means the objection, like "A1". Please see the example.
There's an example:
{{
‘0’: (Zergling, A1)->(Move)->(A4), //It means send Zerglings at A1 to A4
‘1’: (Drone, A1)->(Gather gas)->(Extractor1, A1) // It means send Drones at A1 to gathering gas at Extractor1 at A1
‘2’: (Zergling, A1)->(Morph)->(Baneling) //It means Zergling at A1 need to morph to Baneling
...
}}

For instance:
RESPONSE FORMAT:
1. Current Stage of the Match;
2. Our Zerg Units and Buildings;
3. Our current Zerg Operational Strategy;
4. Opponent's Units and Buildings;
5. Opponent's Tactical Plan and our Potential Risks;
6. Scouting Intel;
7. Analyze based on 'Game Key Decisions Memory' and 'Self-Verification (Avoid problematic commands)'.
8. Based on above analysis, each instruction should follow the below format:
{{
‘0’: (Command Target)->(Action)->(Target),
‘1’: (Command Target)->(Action)->(Target),
‘2’: (Command Target)->(Action)->(Target),
...
}}

        '''
    output1 = llm_gpt35_turbo2(prompt, True)

    return output1


async def overmind_brain_iter(game_time, current_units, current_buildings, current_tech, current_enemy_units,
                              current_enemy_buildings, previous_commands):
    prompt = '''
You are an intelligent brain of Zerg swarm in StarCraft II game.
You are very aggressive and know all the dependencies between Zerg units, Zerg buildings, and Zerg technological research.
You and Terran players are on a square map with 16 mines evenly distributed on the map, as shown in the following matrix:
[[0, B7, B6, B4, B2],
[A8, 0, B5, B3, B1],
[A1, A3, A5, 0, B8],
[A2, A4, A6, A7, 0]]
Currently, your base is at position A1 and the Terran base is at position B1. 0 represents no mine, and other letters represent the mine number.

---Current battle situation
game time: {game_time}

Your current Units consists of:
{{
    {current_units}
    ...
   Omitting means no units
}}

Your current Buildings consists of :
{{
    {current_buildings}
    ...
    Omitting means no Buildings
}}

Your Zerg has developed these technological research:
{{
    {current_tech}
}}

You have detected enemy units in:
{{
    {current_enemy_units}
    ...
    Omitting means no units
}}

You have detected enemy buildings in:
{{
    {current_enemy_buildings}
    ...
    Omitting means no Buildings
}}

---

--- rule
You need to analyze the game progression by following a structured protocol based on the game situation. Make sure to include the following perspectives in your analysis:
1. Current Stage of the Match: Determine the current game stage based on the game time and types of our units, whether it’s early, middle, or late stage.
2. The Condition of Our Forces: Assess our current status in dimensions of:
2.1 Our Zerg Units and Buildings: Scrutinize the state of Zerg Units and Buildings.
2.2 Our Zerg Technology: Analyze the current status of the Zerg technological research based on the unlocked research.
3. Our current Zerg Operational Strategy: Devise a reasonable strategy based on our current situation, opponent’s situation, and scouting intel.
4. Opponent's situation: Assess opponent’s current status in dimensions of:
4.1 Opponent's Units and Buildings: Analyze state of opponent’s Units and Buildings.
4.1 Opponent's Tactical Plan and our Potential Risks: Based on detected opponent’s Units and Buildings, predict the opponent's attack timing to prepare defensive measures in advance.
5. Scouting Intel: Stress the importance of recent and consistent scouting reports to stay updated on the enemy's unit composition, positioning, and possible incoming attacks or expansions.
6. Eliminate Repeated instructions: Based on "Your commands in previous round", analysis which commands are not needed to execute again.
7. Avoid problematic commands: Analysis the problematic commands in "Avoid problematic commands", and avoid the problematic commands this time.
---

---Game Key Decisions Memory
The key decisions in your memory, you can refer to these decisions for strategic deployment.
{{
Based on previous competition experience, you found that:
1. Remember to build Baneling Nest to enable morph Baneling to cause more damage.
2. You can morph many Zerglings to Banelings to cause more damage to the enemy's Marine, Marauder and Siege tanks.
3. You can morph many Roaches to Ravagers to cause more damage to the enemy's Marine, Marauder and Siege tanks.
4. At the early and mid stage of the game, a mixed army of Zergling, Baneling, Roach and Ravager can be unstoppable.
5. Remember to build the Infestation Pit to unlock the build of Lair.
6. Remember to build Hydralisk Den to unlock powerful Hydralisk to cause more damage.
7. Remember to build Ultralisk Cavern to unlock the powerful Ultralisk.
8. Remember to build Greater Spire to unlock the powerful Brood Lord.
}}
---

---Self-Verification (Avoid problematic commands)
These are the experiences you have gained through self-verification, please try to avoid these situations.
{{
'0': (Drone, A1)->(Expand Creep)->(A2)
Problem: Since "Drone" cannot expand creep (only Queens can), this instruction is unreasonable.
'1': (Drone, A1)->(Build)->(Queen Nest, A1)
Problem: This instruction is unreasonable. Drones cannot build Queen Nests; they are constructed by Drones transforming into the structure.
'2': (Drone, A1)->(Build)->(Overlord)
Problem: The problem is that "Drone" cannot hatch "Overlord", only "Larva" can hatch "Overlord".
'3': (Drone, A1)->(Build)->(Drone)
Problem: The problem is that "Drone" cannot hatch "Drone", only "Larva" can hatch "Drone".
}}
---

---Your commands in previous round
{{
    
}}
---

Based on the current battle situation and Units and Buildings from both sides, following the rules above, a brief step-by-step analysis can be done from our strategy, Units and Buildings, economic, technical perspectives, And "Your commands in last round".
Then, formulate 20 actionable, specific decisions (include the target location, like A1, A2, etc.) from the following action list.
These decisions should be numbered from 0, denoting the order in which they ought to be executed, with 0 signifying the most immediate and crucial action.

Note:
1. Game Key Decisions Memory is the key decisions in your memory, you can refer to these decisions for strategic deployment.
2. Self-Verification (Avoid problematic commands) is the experiences you have gained through self-verification, please try to avoid these situations.
3. Please reflect the 'Game Key Decisions Memory' and 'Self-Verification (Avoid problematic commands)' in the analysis of the results.
4. "Command Target" means the unit you want to command, such as "Drone", "Overlord", etc.
"Action" means the actions you want the unit to do, such as "Move", "Morph", etc.
"Target" means the objection, like "A1". Please see the example.
There's an example:
{{
‘0’: (Zergling, A1)->(Move)->(A4), //It means send Zerglings at A1 to A4
‘1’: (Drone, A1)->(Gather gas)->(Extractor1, A1) // It means send Drones at A1 to gathering gas at Extractor1 at A1
‘2’: (Zergling, A1)->(Morph)->(Baneling) //It means Zergling at A1 need to morph to Baneling
...
}}

For instance:
RESPONSE FORMAT:
1. Current Stage of the Match;
2. Our Zerg Units and Buildings;
3. Our current Zerg Operational Strategy;
4. Opponent's Units and Buildings;
5. Opponent's Tactical Plan and our Potential Risks;
6. Scouting Intel;
7. Analyze based on 'Game Key Decisions Memory' and 'Self-Verification (Avoid problematic commands)'.
8. Based on above analysis, each instruction should follow the below format:
{{
‘0’: (Command Target)->(Action)->(Target),
‘1’: (Command Target)->(Action)->(Target),
‘2’: (Command Target)->(Action)->(Target),
...
}}

    '''
    prompt = prompt.format(game_time=game_time, current_units=current_units, current_buildings=current_buildings,
                           current_tech=current_tech, current_enemy_units=current_enemy_units,
                           current_enemy_buildings=current_enemy_buildings)
    print("prompt:\n", prompt)
    output = await llm_gpt35_turbo(prompt, True)

    return output


async def overmind_building_iter(game_time, current_units, current_buildings, current_enemy_units,
                                 current_enemy_buildings, previous_commands):
    prompt = '''
You are an intelligent brain of Zerg swarm in StarCraft II game.
You are very aggressive and know all the dependencies between Zerg units, Zerg buildings, and Zerg technological research.
Your task is to generate construction commands for Zerg buildings.

You and Terran players are on a square map with 16 mines evenly distributed on the map, as shown in the following matrix:
[[0, B7, B6, B4, B2],
[A8, 0, B5, B3, B1],
[A1, A3, A5, 0, B8],
[A2, A4, A6, A7, 0]]
Currently, your base is at position A1 and the Terran base is at position B1. 0 represents no mine, and other letters represent the mine number.

---Current battle situation
game time: {game_time}

The Units you currently have are: {current_units}
The Buildings you currently have are: {current_buildings}

The Enemy Units you curently detect are: {current_enemy_units}
The Enemy Buildings you curently detect are: {current_enemy_buildings}
---

--- rule
You need to analyze the game progression by following a structured protocol based on the game situation. Make sure to include the following perspectives in your analysis:
1. Current Stage of the Match: Determine the current game stage based on the game time and types of our units, whether it’s early, middle, or late stage.
2. The Condition of Our Forces: Assess our current status in dimensions of:
2.1 Our Zerg Units and Buildings: Scrutinize the state of Zerg Units and Buildings.
2.2 Our Zerg Technology: Analyze the current status of the Zerg technological research based on the unlocked research.
3. Our current Zerg Operational Strategy: Devise a reasonable strategy based on our current situation, opponent’s situation, and scouting intel.
4. Opponent's situation: Assess opponent’s current status in dimensions of:
4.1 Opponent's Units and Buildings: Analyze state of opponent’s Units and Buildings.
4.1 Opponent's Tactical Plan and our Potential Risks: Based on detected opponent’s Units and Buildings, predict the opponent's attack timing to prepare defensive measures in advance.
5. Scouting Intel: Stress the importance of recent and consistent scouting reports to stay updated on the enemy's unit composition, positioning, and possible incoming attacks or expansions.
6. Eliminate Repeated instructions: Based on "Your commands in previous round", analysis which commands are not needed to execute again.
7. Avoid problematic commands: Analysis the problematic commands in "Avoid problematic commands", and avoid the problematic commands this time.
---

---Game Key Decisions Memory
The key decisions in your memory, you can refer to these decisions for strategic deployment.
{{
Based on previous competition experience, you found that:
0. Remember to build more hatchery to expend the economy, like (Drone, A1)->(Build)->(Hatchery, A1), (Drone, A1)->(Build)->(Hatchery, A2), (Drone, A1)->(Build)->(Hatchery, A3).
1. Remember to build Baneling Nest to enable morph Baneling to cause more damage.
2. You can morph many Zerglings to Banelings to cause more damage to the enemy's Marine, Marauder and Siege tanks.
3. You can morph many Roaches to Ravagers to cause more damage to the enemy's Marine, Marauder and Siege tanks.
4. At the early and mid stage of the game, a mixed army of Zergling, Baneling, Roach and Ravager can be unstoppable.
5. Remember to build the Infestation Pit to unlock the build of Lair.
6. Remember to build Hydralisk Den to unlock powerful Hydralisk to cause more damage.
7. Remember to build Ultralisk Cavern to unlock the powerful Ultralisk.
8. Remember to build Greater Spire to unlock the powerful Brood Lord.
}}

---Self-Verification (Avoid problematic commands)
These are the experiences you have gained through self-verification, please try to avoid these situations.
{{
'0': (Drone, A1)->(Expand Creep)->(A2)
Problem: Since "Drone" cannot expand creep (only Queens can), this instruction is unreasonable.
'1': (Drone, A1)->(Build)->(Queen Nest, A1)
Problem: This instruction is unreasonable. Drones cannot build Queen Nests; they are constructed by Drones transforming into the structure.
'2': (Drone, A1)->(Build)->(Overlord)
Problem: The problem is that "Drone" cannot hatch "Overlord", only "Larva" can hatch "Overlord".
'3': (Drone, A1)->(Build)->(Drone)
Problem: The problem is that "Drone" cannot hatch "Drone", only "Larva" can hatch "Drone".
}}
---

---Your commands in previous round
{{
    
}}
---

Based on the current battle situation and Units and Buildings from both sides, following the rules above, a brief step-by-step analysis can be done from our strategy, Units and Buildings, economic, technical perspectives, And "Your commands in last round".
Then, formulate 20 actionable, specific decisions (include the target location, like A1, A2, etc.) from the following action list.
These decisions should be numbered from 0, denoting the order in which they ought to be executed, with 0 signifying the most immediate and crucial action.

Note:
1. Game Key Decisions Memory is the key decisions in your memory, you can refer to these decisions for strategic deployment.
2. Self-Verification (Avoid problematic commands) is the experiences you have gained through self-verification, please try to avoid these situations.
3. Please reflect the 'Game Key Decisions Memory' and 'Self-Verification (Avoid problematic commands)' in the analysis of the results.
4. "Command Target" means the unit you want to command, such as "Drone", "Overlord", etc.
"Action" means the actions you want the unit to do, such as "Move", "Morph", etc.
"Target" means the objection, like "A1". Please see the example.
There's an example:
{{
‘0’: (Zergling, A1)->(Move)->(A4), //It means send Zerglings at A1 to A4
‘1’: (Drone, A1)->(Gather gas)->(Extractor1, A1) // It means send Drones at A1 to gathering gas at Extractor1 at A1
‘2’: (Zergling, A1)->(Morph)->(Baneling) //It means Zergling at A1 need to morph to Baneling
...
}}

For instance:
RESPONSE FORMAT:
1. Current Stage of the Match;
2. Our Zerg Units and Buildings;
3. Our current Zerg Operational Strategy;
4. Opponent's Units and Buildings;
5. Opponent's Tactical Plan and our Potential Risks;
6. Scouting Intel;
7. Analyze based on 'Game Key Decisions Memory' and 'Self-Verification (Avoid problematic commands)'.
8. Based on above analysis, each instruction should follow the below format:
{{
‘0’: (Command Target)->(Action)->(Target),
‘1’: (Command Target)->(Action)->(Target),
‘2’: (Command Target)->(Action)->(Target),
...
}}
    '''
    prompt = prompt.format(game_time=game_time, current_units=current_units, current_buildings=current_buildings,
                           current_enemy_units=current_enemy_units,
                           current_enemy_buildings=current_enemy_buildings)
    print("Building prompt:\n", prompt)
    output = await llm_gpt35_turbo(prompt, True)

    return output


async def overmind_attack_module(game_time, current_units, army_damage, current_enemy_units,
                                 current_enemy_buildings, enemy_damage):
    prompt = '''
You are an intelligent brain of Zerg swarm in StarCraft II game.
You are very aggressive and know all the dependencies between Zerg units, Zerg buildings, and Zerg technological research.

---Current battle situation
game time: {game_time}

You have: {current_units}.
The total damage of your army: {army_damage}.
Enemy units you currently detect are: {current_enemy_units}.
The Enemy buildings you currently detect are: {current_enemy_buildings}.
The total damage of enemy army: {enemy_damage}.

---

--- rule
You need to analyze the suitable time to attack enemy by following a structured protocol based on the game situation. Make sure to include the following perspectives in your analysis:
1. Our Zerg Units: Based on the current match stage, analyze whether the current status of Zerg units to suitable to launch an attack.
2. Enemy's Units: First analyze the enemy's units , and then analyze whether the our Zerg units can defeat the enemy's units.
3. Enemy's Buildings: Based on the enemy's buildings, analyze the enemy's strategy.
4 Current Stage of the Match: Determine the current game stage based on the game time and types of our units, whether it’s early, middle, or late stage.
5. Whether to attack: True if it is appropriate to launch an attack now, False otherwise.
---

---Game Key Decisions Memory
The key decisions in your memory, you can refer to these decisions for strategic deployment.
{{
Based on previous competition experience, you found that:

}}
---

Based on the Units and Buildings from both sides, following the rules above, a brief step-by-step analysis can be done from Zerg units and buildings,  technical perspectives, and Enemy's units and buildings.

Note:
1. Game Key Decisions Memory is the key decisions in your memory, you can refer to these decisions for strategic deployment.

For instance:
RESPONSE FORMAT:
1. Our Zerg Units;
2. Enemy's Units;
3. Enemy's Buildings;
4. Current Stage of the Match;
5. Whether to attack;
6. True (if it's the suitable time to attack, otherwise is false)
    '''
    prompt = prompt.format(game_time=game_time, current_units=current_units, army_damage=army_damage,
                           current_enemy_units=current_enemy_units,
                           current_enemy_buildings=current_enemy_buildings,
                           enemy_damage=enemy_damage)
    print("Attack prompt:\n", prompt)
    output = await llm_gpt35_turbo(prompt, True)

    return output


if __name__ == '__main__':
    situation__ = '''
    You are an intelligent brain of Zerg swarm in StarCraft II game.
    You are very aggressive and know all the dependencies between Zerg units, Zerg buildings, and Zerg technological research.
    You and Terran players are on a square map with 16 mines evenly distributed on the map, as shown in the following matrix:
    [[0, B7, B6, B4, B2],
    [A8, 0, B5, B3, B1],
    [A1, A3, A5, 0, B8],
    [A2, A4, A6, A7, 0]]
    Currently, your base is at position A1 and the Terran base is at position B1. 0 represents no mine, and other letters represent the mine number.

    ---Current battle situation
    game time: 00:35
    Your current Units consists of:
    {
    At point A1, there are: 16 Drones are gathering minerals in Hatchery, 1 Overlord are idling;
	...
	Omitting means no units
    }

    Your current Buildings consists of :
    {
    At point A1, there are: 1 Hatchery, 1 Extractor, 1 Evolution Chamber;
    ...
    Omitting means no Buildings
    }

    Your Zerg has developed these technological research:
    {
    None
    }

    You have detected enemy units in:
    {
    At point B1, there are: Unknown;
    ...
    Omitting means no units
    }

    You have detected enemy buildings in:
    {
    At point B1, there are: Unknown;
    ...
    Omitting means no Buildings
    }
    ---

    --- rule
    You need to analyze the game progression by following a structured protocol based on the game situation. Make sure to include the following perspectives in your analysis:
    1. Current Stage of the Match: Determine the current game stage based on our situation and opponent’s status you detected, whether it’s early, middle, or late stage.
    2. The Condition of Our Forces: Assess our current status in dimensions of:
    2.1 Our Zerg Units and Buildings: Scrutinize the state of Zerg Units and Buildings.
    2.2 Our Zerg Technology: Analyze the current status of the Zerg technological research based on the unlocked research.
    technology tree based on the Zerg Units and Buildings
    3. Our current Zerg Operational Strategy: Devise a reasonable strategy based on our current situation, opponent’s situation, and scouting intel.
    4. Opponent's situation: Assess opponent’s current status in dimensions of:
    4.1 Opponent's Units and Buildings: Analyze state of opponent’s Units and Buildings.
    4.1 Opponent's Tactical Plan and our Potential Risks: Based on detected opponent’s Units and Buildings, predict the opponent's attack timing to prepare defensive measures in advance.
    5. Scouting Intel: Stress the importance of recent and consistent scouting reports to stay updated on the enemy's unit composition, positioning, and possible incoming attacks or expansions.
    6. Eliminate Repeated instructions: Based on "Your commands in previous round", analysis which commands are not needed to execute again.
    7. Avoid problematic commands: Analysis the problematic commands in "Your problematic commands in previous rounds", and avoid the problematic commands this time.
    ---

    ---Your commands in previous round
    {

    }
    ---

    ---Your problematic commands in previous rounds
    {
    '0': (Drone, A1)->(Expand Creep)->(A2)
    ANSWER: Since "Drone" cannot expand creep (only Queens can), this instruction is unreasonable.
    '1': (Drone, A1)->(Build)->(Queen Nest, A1)
    ANSWER: This instruction is unreasonable. Drones cannot build Queen Nests; they are constructed by Drones transforming into the structure.
    }
    ---


    Based on the current battle situation and Units and Buildings from both sides, following the rules above, a brief step-by-step analysis can be done from our strategy, Units and Buildings, economic, technical perspectives, And "Your commands in last round".
    Then, formulate 20 actionable, specific decisions (include the target location, like A1, A2, etc.) from the following action list.
    These decisions should be numbered from 0, denoting the order in which they ought to be executed, with 0 signifying the most immediate and crucial action.


    For instance:

    RESPONSE FORMAT:
    1. Current Stage of the Match;
    2. Our Zerg Units and Buildings;
    3. Our current Zerg Operational Strategy;
    4. Opponent's Units and Buildings;
    5. Opponent's Tactical Plan and our Potential Risks;
    6. Scouting Intel;
    7. Eliminate Repeated instructions;
    8. Avoid problematic commands;
    9. Based on above analysis, each instruction should follow the below format:
    {
    ‘0’: (Command Target)->(Action)->(Target),
    ‘1’: (Command Target)->(Action)->(Target),
    ‘2’: (Command Target)->(Action)->(Target),
    ...
    }
    Note: "Command Target" means the unit you want to command, such as "Drone", "Overlord", etc.
    "Action" means the actions you want the unit to do, such as "Move", "Morph", etc.
    "Target" means the objection, like "A1". Please see the example.
    There's an example:
    {
    ‘0’: (Zergling, A1)->(Move)->(A4), //It means send Zerglings at A1 to A4
    ‘1’: (Drone, A1)->(Gather gas)->(Extractor1, A1) // It means send Drones at A1 to gathering gas at Extractor1 at A1
    ‘2’: (Zergling, A1)->(Morph)->(Baneling) //It means Zergling at A1 need to morph to Baneling
    ...
    }


'''

    prompt = situation__

    res = llm_gpt35_turbo(prompt, True)
    print('res is ', res)
