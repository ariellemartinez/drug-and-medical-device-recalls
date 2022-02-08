import unicodedata
import re
import requests
import pandas as pd

def slugify(value, allow_unicode=False):
	# Taken from https://github.com/django/django/blob/master/django/utils/text.py
	value = str(value)
	if allow_unicode:
		value = unicodedata.normalize("NFKC", value)
	else:
		value = unicodedata.normalize("NFKD", value).encode(
			"ascii", "ignore").decode("ascii")
	value = re.sub(r"[^\w\s-]", "", value.lower())
	return re.sub(r"[-\s]+", "-", value).strip("-_")

# All ZIP codes in Nassau and Suffolk counties start with the digits 110, 115, 117, 118, or 119.
three_digit_zip_codes = ["110", "115", "117", "118", "119"]

# We are defining the openFDA datasets we want to scrape here.
datasets = [
	{
		"slug": "drug",
		# "dataset_link": "https://www.accessdata.fda.gov/scripts/ires/index.cfm",
		# "api_documentation_link": "https://open.fda.gov/apis/drug/enforcement/",
		"description": "Drug recalls",
		"dictionary_values": ["openfda"]
	}, {
		"slug": "device",
		# "dataset_link": "https://www.accessdata.fda.gov/scripts/ires/index.cfm",
		# "api_documentation_link": "https://open.fda.gov/apis/device/enforcement/",
		"description": "Medical device recalls",
		"dictionary_values": ["openfda"]
	} 
]

# We are going to call every item within "datasets" a "dataset". As we go through each dataset, we are going to scrape the dataset.
for dataset in datasets:
	try:
		# We are creating an empty list called "results".
		results = []
		url = "https://api.fda.gov/" + dataset["slug"]  + "/enforcement.json"
		# The limit can be up to 1000.
		limit = 1000
		# Start the offset at 0.
		offset = 0
		initial_payload = 'limit=' + str(limit) + '&skip=' + str(offset) + '&search=state:"NY"'
		# "requests" documentation page is here: https://docs.python-requests.org/en/master/user/quickstart/
		initial_request = requests.get(url, params=initial_payload)
		# As we go through each page of the dataset, we are going to scrape that page of the dataset.
		count = initial_request.json()["meta"]["results"]["total"]
		i = 0
		while i < count / limit:
			offset = i * limit
			loop_payload = 'limit=' + str(limit) + '&skip=' + str(offset) + '&search=state:"NY"'
			loop_request = requests.get(url, params=loop_payload)
			for result in loop_request.json()["results"]:
				for dictionary_value in dataset["dictionary_values"]:
					result.pop(dictionary_value)
				# ZIP codes 11004 and 11005 are both in Queens and should be excluded.
				if result["postal_code"][0:3] in three_digit_zip_codes and result["postal_code"][0:5] != "11004" and result["postal_code"][0:5] != "11005":
					results.append(result)
			i += 1
		# "pandas" documentation page is here: https://pandas.pydata.org/docs/index.html
		df = pd.DataFrame(results)
		file_name = slugify(dataset["description"])
		df.to_csv("csv/" + file_name + ".csv", index=False)
	except:
		pass