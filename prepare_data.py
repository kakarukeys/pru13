from __future__ import division
import json

pru12_data = json.load(open("data/pru12_parliament.json"))
data = json.load(open("data/pru13_parliament.json"))
state_data = json.load(open("data/pru13_state.json"))
demographics = json.load(open("data/pru13_demographics.json"))

def get_BN_votes(candidates):
	try:
		return (c["votes"] for c in candidates if c["party"] == "BN").next()
	except StopIteration:
		return (c["votes"] for c in candidates if c["party"] == "BEBAS").next()	#BN-friendly candidate

def prepare(record):
	demographics_details = demographics[record["state"]]["parliament_constituencies"][record["constituency_code"]]
	pru12_total_registered_voters = (
		r["total_registered_voters"] 
			for r in pru12_data if 
				r["constituency_code"] == record["constituency_code"]
	).next()
	state_codes = demographics_details["state_constituencies"].keys()
	BN_votes = get_BN_votes(record["candidates"])

	try:
		total_state_BN_votes = sum([
			get_BN_votes(r["candidates"])
				for r in state_data if 
					r["constituency_code"] in state_codes and r["state"] == record["state"]
		])
	except StopIteration:	#constituencies that have no state seats or election
		total_state_BN_votes = 0

	return {
		"name": record["constituency_code"] + ' ' + record["constituency_name"],
		"%_BN_vote": BN_votes * 100 / 
			(record["ballot_sheets_issued"] - record["unreturned_ballot_sheets"]),
		"voters_turnout": record["voters_turnout"],
		"3G_penetration": demographics_details["3G_penetration"],
		"metropolitan_index": demographics_details["metropolitan_index"],
		"%_Malay": demographics_details["racial_breakdown"]["Malay"],
		"%_Chinese": demographics_details["racial_breakdown"]["Chinese"],
		"%_Indian": demographics_details["racial_breakdown"]["Indian"],
		"%_BP_Sabah": demographics_details["racial_breakdown"]["Bumiputra Sabah"],
		"%_BP_Sarawak": demographics_details["racial_breakdown"]["Bumiputra Sarawak"],
		"%_change_total_registered_voters": (record["total_registered_voters"] - pru12_total_registered_voters) * 100 / pru12_total_registered_voters,
		"%_margin": record["majority"] * 100 / (c["votes"] for c in record["candidates"] if c["status"] == "MENANG").next(),
		"%_BN_parliament_state_vote_deviation": (BN_votes - total_state_BN_votes) * 100 / BN_votes,
		"total_registered_voters": record["total_registered_voters"],
	}

final_data = map(prepare, data)

with open("final_data.csv", 'w') as f:
	f.write(','.join(final_data[0].keys()) + '\n')
	for record in final_data:
		f.write(','.join(map(str, record.values())) + '\n')
