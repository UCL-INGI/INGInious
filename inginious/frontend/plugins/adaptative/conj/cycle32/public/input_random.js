$.getJSON("/course/conj/cycle32/file.json", function(data) {

//data is the JSON string
var i = parseInt(input["@random"][0] * data.random_tab.length);  
document.getElementById("verb").innerHTML = data.random_tab[i];
var j = parseInt(input["@random"][1] * data.random_tab_person.length);    
document.getElementById("pers").innerHTML = data.random_tab_person[j];
var k = parseInt(input["@random"][2] * data.random_tab_tenses.length);    
document.getElementById("tense").innerHTML = data.random_tab_tenses[k];
});
    
