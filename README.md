Simple Agent Final is a simple and efficient agent system that combines a powerful core and many modules/tools that can be flexibly combined or new ones created.


## How to use

Install requirements
```
pip install -r requirements.txt
```
Set up the API keys in .env and load dotenv in the biggining of code:
```
from dotenv import load_dotenv
load_dotenv(".env")
```

### Quike start.
```
from core.agent import Agent

ag = Agent(history=['u', 'hi'], model_name="provider_name/model_name")
response = ag.chat()
print(response)
```

#### Tools using

```
history = [
    ['u', 'use ls']
]

ag = Agent(history=history,
    model_name="provider_name/model_name",
    cwd="~",
    preset="tools")

print(ag.chat(loop=1)
ag.add("make screenshot")
print(ag.chat(loop=2)
```

#### Chat Saving 

```
import json

with open('chat.json', 'w', encoding='utf-8') as f:
    json.dump(ag.client.history, f, ensure_ascii=False, indent=4)
```
after that...
```streamlit run app.py```

- *Native saving is planned*


# LICENSE


This project is distributed under a custom license. By using, forking, or modifying this software, you agree to the following mandatory naming condition.

For full details, please read the [LICENSE](LICENSE) file.