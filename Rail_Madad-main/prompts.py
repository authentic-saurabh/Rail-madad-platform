import json
with open('categories.json', 'r') as file:
    data = json.load(file)
with open('department.json', 'r') as file:
    dept = json.load(file)

prompt1 = f'''We are making a webapp that allows users to lodge complaints regarding
their train travels easily and quickly. We want people to upload a photo and
categorize what complaint they are trying to share and generate a description
of that.
Here are all the problem types and subtypes: {data}
You need to analyze the image and if you are confident, predict the type and
subtype of the problem and generate a description, else return 0.

Here is the format of the output:
If confident about analysis:
{{
"type":"Security",
"subtype":"Theft of Passengers Belongings/Snatching",
"details":"a person is trying to snatch the bag off of a lady's shoulder forcefully."
}}

If not confident:
{{
"type":"0"
}}

Strictly adhere to this output format, no code block, no nothing, just the JSON response in the format I just gave you.
'''

prompt2=f'''We are making a webapp that allows users to lodge complaints regarding
their train travels easily and quickly. We want people to type their issues and
categorize what complaint they are trying to share and generate a description
of that.
Here are all the problem types and subtypes: {data}
You need to analyze their issue and if you are confident, predict the type and
subtype of the problem and generate a description, else return 0.

Here is the format of the output:
If confident about analysis:
{{
"type":"Security",
"subtype":"Theft of Passengers Belongings/Snatching",
"details":"a person is trying to snatch the bag off of a lady's shoulder forcefully."
}}

If not confident:
{{
"type":"0"
}}

Strictly adhere to this output format, no code block, no nothing, just the JSON response in the format I just gave you.
here is the text :
'''

prompt3=f'''We are making a webapp that allows users to lodge complaints regarding
their train travels easily and quickly. people are giving us problem details, problem types and other details, we want to access their severity and assign a department to the complaint
Here are all the problem types and their respective departments: {dept}
You need to analyze their issue type and predict the severity and department for the problem type.
severity can be either low, medium or high
cases that are mere inconviniences are ranked low, like fan not working, bedsheets not available,etc.
cases that might become a huge problem if not solved can be categorized as medium, like water not available, fight between passengers etc.
cases that are against ethical practices of our society or cant be ignored should be categorized high, like theft, assault, medical needs, bribery etc.
Here is the format of the output:
{{
"severity":"high",
"department":"Security"
}}

Strictly adhere to this output format, no code block, no nothing, just the JSON response in the format I just gave you.
here is the data :
'''

