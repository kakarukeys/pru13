import json
from functools import partial

import requests
from bs4 import BeautifulSoup

from cleanup import json_list
from scrape2 import KODS_STATE
from utils import levenshtein

def save(data):
	with open("pru13_demographics.json", 'w') as f:
		json.dump(data, f)

statistik = list(open("data/STATISTIK_UMUM_PILIHANRAYA.txt"))

def get_sarawak_state_seats(parliament_constituency_code):
	extracting = False
	constituency_codes = []
	constituency_names = []
	for no, line in enumerate(statistik):
		if not extracting and "..." + parliament_constituency_code in line:
			extracting = True
		elif extracting and "..." in line:
			break
		elif extracting and "DUN" in line:
			for i in range(1, 6):
				if "Nama Dun" in statistik[no + i]:
					break
				else:
					constituency_codes.append(statistik[no + i].strip())
		elif extracting and "Nama Dun" in line:
			for i in range(1, 6):
				if "Kategori Pemilih" in statistik[no + i]:
					break
				else:
					constituency_names.append(statistik[no + i].strip().upper())
	return dict(zip(constituency_codes, ({"name": name} for name in constituency_names))) 

	result = dict(zip(collected_races, collected_percentages))
	if abs(sum(result.values()) - 100) > 0.03:
		raise Exception("percentages do not sum up to 100% in parliament_constituency_code: {0}\n{1}".format(parliament_constituency_code, result))
	else:
		return result

PS_LOOKUP = {}
for k in KODS_STATE:
	PS_LOOKUP.setdefault("P." + k[:3].lstrip('0'), []).append("N." + k[3:].lstrip('0'))

data = {}
for j in json_list[2]:
	pcs = data.setdefault(j["state"], {}).setdefault("parliament_constituencies", {})
	pc = pcs[j["constituency_code"]] = {"name": j["constituency_name"]}
	if j["constituency_code"] in PS_LOOKUP:
		pc["state_constituencies"] = dict((code, None) for code in PS_LOOKUP[j["constituency_code"]])
	elif j["state"] == "SARAWAK":
		pc["state_constituencies"] = get_sarawak_state_seats(j["constituency_code"])
	else:
		pc["state_constituencies"] = {}

SP_LOOKUP = {}
for s in data:
	pcs = data[s]["parliament_constituencies"]
	for pc in pcs:
		scs = pcs[pc]["state_constituencies"]
		for sc in scs:
			SP_LOOKUP[(s, sc)] = pc

for j in json_list[3]:
	data[j["state"]]["parliament_constituencies"][SP_LOOKUP[(j["state"], j["constituency_code"])]]["state_constituencies"][j["constituency_code"]] = {"name": j["constituency_name"]}

save(data)

"""
URL_PARLIAMENT = "http://ww2.utusan.com.my/utusan/special.asp?pr=PilihanRaya2013&pg=keputusan/{0}.htm"
URL_STATE = "http://ww2.utusan.com.my/utusan/special.asp?pr=PilihanRaya2013&pg=keputusan/Johor_N3.htm"

def gen_utusan_code(state, parliament_constituency_code):
	utusan_state = "wilayahpersekutuan" if state.startswith('W.P.') else state.lower().replace(' ', '')
	utusan_pcc = parliament_constituency_code.lower().replace('.', '')
	return utusan_state + '_' + utusan_pcc

UTUSAN_RACE_CODES = {
	'C': "Chinese",
	'M': "Malay",
	'I': "Indian",
	'L': "Others",
}

def get_racial_breakdown_utusan(state, parliament_constituency_code):
	r = requests.get(URL_PARLIAMENT.format(gen_utusan_code(state, parliament_constituency_code)))
	soup = BeautifulSoup(r.text)

	b_tags = soup.select("div#wrap_center b")
	racial_breakdown_string = (tag for tag in b_tags if tag.text.startswith("Pecahan Kaum")).next().next_sibling.strip()

	racial_breakdown = {}
	for fragment in racial_breakdown_string.split():
		race_code, percentage = fragment.split(':')
		racial_breakdown[UTUSAN_RACE_CODES[race_code]] = int(percentage.replace('%', ''))

	return racial_breakdown
"""

RACES = {
	"Melayu": "Malay",
	"Cina": "Chinese",
	"India": "Indian",
	"BP Sabah": "Bumiputra Sabah",
	"BP Sarawak": "Bumiputra Sarawak",
	"Orang Asli": "Orang Asli",
	"Lain-lain": "Others",
}

def get_racial_breakdown_statistik(parliament_constituency_code):
	extracting = False
	collected_races = []
	collected_percentages = []
	for no, line in enumerate(statistik):
		if not extracting and "..." + parliament_constituency_code in line:
			extracting = True
		elif extracting and "..." in line:
			break
		elif extracting:
			if '%' in line:
				collected_percentages.append(float(line.strip().replace('%', '')))
			else:
				for rc in RACES:
					if rc.lower() in line.lower():
						collected_races.append(RACES[rc])
	result = dict(zip(collected_races, collected_percentages))
	if abs(sum(result.values()) - 100) > 0.03:
		raise Exception("percentages do not sum up to 100% in parliament_constituency_code: {0}\n{1}".format(parliament_constituency_code, result))
	else:
		return result

def parse_gazetteer(line):
	info = line.split('\t')[:3]
	return info[0], int(info[1]), int(info[2])

cities_and_towns = map(parse_gazetteer, open("data/World_Gazetteer.txt"))

def get_metropolitan_index(cname):
	cname = cname.lower()
	for suffix in ("utara", "selatan", "timor", "barat"):
		cname = cname.replace(' ' + suffix, '')
	results = sorted([(levenshtein(name, cname), name, index) for name, population, index in cities_and_towns])
	if results[0][0] < 2:
		return max(results[0][2], 2), results[0][1]
	else:
		return 2, ''

for s in data:
	pcs = data[s]["parliament_constituencies"]
	for pc in pcs:
		obj = pcs[pc]
		obj["racial_breakdown"] = get_racial_breakdown_statistik(pc)

		scs = obj["state_constituencies"]
		for sc in scs:
			SP_LOOKUP[(s, sc)] = pc

		names = [obj["name"]] + [sobj["name"] for sobj in scs.values()]
		if "W.P." in s: names.append(s[5:])
		query_results = max(map(get_metropolitan_index, names), key=lambda p: p[0])
		print "{0} includes a city or town {1} of metropolitan index {2}".format(names, query_results[1], query_results[0])
		obj["metropolitan_index"] = query_results[0]

save(data)