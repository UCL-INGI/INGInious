"""
	Written by Naitali Brandon 
	Last modification: 29/04
	
	This file provides some utilities for manipulating verbal forms, using Grammalecte library.
	
"""
from gramm.grammalecte.fr.conj import Verb
import sys

# Dictionary of map between the lisible form and its Grammalecte code
str_to_code = {
	"indicatif présent" : ":Ip",
	"indicatif imparfait" : ":Iq",
	"imperatif présent" : ":E",
	"indicatif futur simple" : ":If",
	"conditionnel présent" : ":K",
	"indicatif passé simple" : ":Is",
	"subjonctif présent" : ":Sp",
	"participe présent" : ":P",
	"participe passé" : ":Q",
	"première personne du singulier" : ":1s",
	"deuxième personne du singulier" : ":2s",
	"troisième personne du singulier" : ":3s",
	"première personne du pluriel" : ":1p",
	"deuxième personne du pluriel" : ":2p",
	"troisième personne du pluriel" : ":3p",
	"infinitif" : ":"
}


"""
	@param 
		verb is a string representing a verb at the infinitive form, like "manger"
		to_know is the verb form from which we want to get the tense, like "mangerai"
		
	@return 
		a list of tuples of possibles tenses for the verbal form given in argument in the form:
			[(tense_code, person_code), ...]
"""
def get_conj(verbe, to_know):
	verb = Verb(verbe)
	possibles_tenses = []
	all_conj = verb.dConj
	for i in all_conj:
		for j in all_conj[i]:
			if(all_conj[i][j] == to_know):
				possibles_tenses.append((i, j))
	return possibles_tenses
	
	
"""
	@param 
		tense is the Grammalecte code corresponding to the tense we want to conjugate, like ":Ip" for "indicatif présent"
		person is the Gramalecte code corresponding to the person we want to conjugate, like ":1s" for "première personne du singulier".
		verb is the verb we want to conjugate, at infinitive form, like "manger"
	
	@return 
		the conjugated form of verb, like "mange"
"""
def conjugate(tense, person, verb):
	verb = Verb(verb)
	return verb.dConj[tense][person]
	

"""
	@param 
		name is a lisible form of a tense or a person like "indicatif présent" or "première personne du singulier"
	@return
		the Grammalecte code in the str_to_code dictionary
"""
def string_to_code(name):
	return str_to_code[name]

