import json, decimal

FILENAMES = ("pru12_parliament.json", "pru12_state.json", "pru13_parliament.json", "pru13_state.json")

def open_files():
	return [json.load(open('data/' + name)) for name in FILENAMES]

def save(json_list):
	for j, name in zip(json_list, FILENAMES):
		with open('data/' + name, 'w') as f:
			json.dump(j, f)

def trim_turnout(j):
	for obj in j:
		obj["voters_turnout"] = float(obj["voters_turnout"])
	return min(j, key=lambda a: a["voters_turnout"])["voters_turnout"], max(j, key=lambda a: a["voters_turnout"])["voters_turnout"]

def check_constituency_code(j):
	codes = set(map(lambda a: a["constituency_code"], j))
	return codes

def check_constituency_name(j):
	pair = set(map(lambda a: (a["constituency_code"], a["constituency_name"]), j))
	return pair

def check_state_constituency_name(j):
	memo = {}
	for obj in j:
		pair = (obj["state"], obj["constituency_code"])
		if pair in memo and memo[pair] != obj["constituency_name"]:
			raise Exception("state: {0}, constituency_code: {1}, names: {2}, {3}".format(obj["state"], obj["constituency_code"], obj["constituency_name"], memo[pair]))
		else:
			memo[pair] = obj["constituency_name"]

def trim_state(j):
	for obj in j:
		if obj["state"] in ("KUALA LUMPUR", "LABUAN", "PUTRAJAYA"):
			obj["state"] = "W.P. " + obj["state"]
	return set(map(lambda a: a["state"], j))

def trim_total(j):
	for obj in j:
		obj["total_registered_voters"] = int(obj["total_registered_voters"])
	return min(j, key=lambda a: a["total_registered_voters"])["total_registered_voters"], max(j, key=lambda a: a["total_registered_voters"])["total_registered_voters"]

def trim_majority(j):
	for obj in j:
		obj["majority"] = int(obj["majority"])
	return min(j, key=lambda a: a["majority"])["majority"], max(j, key=lambda a: a["majority"])["majority"]

STRING_ATTRIBUTES = ("winner_party", "winner_name", "constituency_code", "constituency_name", "state")
CANDIDATE_STRING_ATTRIBUTES = ("status", "party", "name")
def trim_string(j):
	for obj in j:
		for a in STRING_ATTRIBUTES:
			obj[a] = obj[a].upper().strip()
		for c in obj["candidates"]:
			for a in CANDIDATE_STRING_ATTRIBUTES:
				c[a] = c[a].upper().strip()

INTEGER_ATTRIBUTES = ("total_registered_voters", "majority", "spoilt_votes", "unreturned_ballot_sheets", "ballot_sheets_issued")
CANDIDATE_INTEGER_ATTRIBUTES = ("votes",)
def convert_integers(j):
	for obj in j:
		for a in INTEGER_ATTRIBUTES:
			obj[a] = int(obj[a])
		for c in obj["candidates"]:
			for a in CANDIDATE_INTEGER_ATTRIBUTES:
				c[a] = int(c[a])

def calc_turnout(j):
	for obj in j:
		turnout = float(obj["ballot_sheets_issued"]) / obj["total_registered_voters"] * 100
		obj["voters_turnout"] = round(decimal.Decimal(turnout), 2)

def get_winner(obj):
	try:
		return (c for c in obj["candidates"] if c["status"] == "MENANG").next()
	except StopIteration:
		raise Exception("no winner for state: {0}, constituency_name: {1}".format(obj["state"], obj["constituency_name"]))

def get_losers(obj):
	return filter(lambda c: c["status"] != "MENANG", obj["candidates"])

def get_total_votes(obj):
	return sum(map(lambda c: c["votes"], obj["candidates"])) + obj["spoilt_votes"]

def set_loser_status(j):
	for obj in j:
		losers = get_losers(obj)
		for l in losers:
			l["status"] = u"KALAH"

def check_winner(j):
	for obj in j:
		winner = get_winner(obj)
		losers = get_losers(obj)
		if winner["votes"] <= max(map(lambda c: c["votes"], losers) or [-1]):
			raise Exception("winner is not winner: {0}".format(obj["winner_name"]))

		if obj["winner_name"] != winner["name"]:
			raise Exception("winner_name: {0}, {1} for state: {2}, constituency_name: {3}".format(obj["winner_name"], winner["name"], obj["state"], obj["constituency_name"]))

		if obj["winner_party"] != winner["party"]:
			raise Exception("winner_party: {0}, {1} for state: {2}, constituency_name: {3}".format(obj["winner_party"], winner["party"], obj["state"], obj["constituency_name"]))

def check_majority(j):
	for obj in j:
		if len(obj["candidates"]) == 1:
			majority = 0
		else:
			winner = get_winner(obj)
			losers = get_losers(obj)
			majority = int(winner["votes"]) - max(map(lambda c: int(c["votes"]), losers))
		if majority != obj["majority"]:
			print "majority incorrect for state: {0}, constituency_name: {1}".format(obj["state"], obj["constituency_name"])

def check_parties(j):
	all_parties = set()
	for obj in j:
		for c in obj["candidates"]:
			all_parties.add(c["party"])
	print all_parties

def check_ubs(j):
	for obj in j:
		total_votes = get_total_votes(obj)
		if obj["unreturned_ballot_sheets"] != obj["ballot_sheets_issued"] - total_votes:
			print "votes tally incorrect for state: {0}, constituency_name: {1}".format(obj["state"], obj["constituency_name"])

def check_turnout(j):
	for obj in j:
		turnout = float(obj["ballot_sheets_issued"]) / obj["total_registered_voters"] * 100
		if abs(obj["voters_turnout"] - turnout) > 0.49:
			print "turnout incorrect for state: {0}, constituency_name: {1}, turnout = {2}, {3}".format(obj["state"], obj["constituency_name"], turnout, obj["voters_turnout"])
		if turnout < 0 or turnout >= 100:
			print "turnout out of range for state: {0}, constituency_name: {1}, turnout = {2}, {3}".format(obj["state"], obj["constituency_name"], turnout, obj["voters_turnout"])

json_list = open_files()
for j in json_list:
	trim_string(j)
	convert_integers(j)

	result = trim_turnout(j)
	print result

	result = trim_state(j)
	print result
	print len(result)

	result = trim_total(j)
	print result

	result = trim_majority(j)
	print result

	set_loser_status(j)
	pass

for j in json_list[0:2]:
	calc_turnout(j)

codes = reduce(set.union, map(check_constituency_code, json_list[::2]))
print codes
print len(codes)
codes = reduce(set.union, map(check_constituency_code, json_list[1::2]))
print codes
print len(codes)

pair = reduce(set.union, map(check_constituency_name, json_list[::2]))
print pair
print len(pair)
pair = reduce(set.union, map(check_constituency_name, json_list[1::2]))
print pair
print len(pair)

check_state_constituency_name(json_list[1] + json_list[3])
for j in json_list:
	check_winner(j)
	check_majority(j)
	check_parties(j)
	check_ubs(j)
	check_turnout(j)

#save(json_list)
