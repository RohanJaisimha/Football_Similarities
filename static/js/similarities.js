$(document).ready(function () {
    $("#search_box").selectize({
        sortField: "text"
    });
});
function findSimilarities() {
    let player_name = getPlayerName();
    let attributes_to_consider = getAttributesToConsider();
    let teams_to_consider = getTeamsToConsider();
    let positions_to_consider = getPositionsToConsider();
    let min_age = getMinAge();
    let max_age = getMaxAge();
    let k = getK();
    if(!validateInput(player_name, attributes_to_consider, teams_to_consider, positions_to_consider)) {
        return;
    }
    if(max_age < min_age) {
        let t = max_age;
        max_age = min_age;
        min_age = t;
    }
    let request = $.ajax({
        url: "/findSimilarities",
        type: "post",
        data: {
            "player_name": player_name,
            "attributes_to_consider": JSON.stringify(attributes_to_consider),
            "teams_to_consider": JSON.stringify(teams_to_consider),
            "positions_to_consider": JSON.stringify(positions_to_consider), 
            "min_age": min_age,
            "max_age": max_age,
            "k": k
        }
    });
    request.done(function(response, textStatus, XHR) {
        response = JSON.parse(response);
        console.log(response);
        let results_table_area = document.getElementById("results_table_area");
        results_table_html = "<table id='results_table' border='1'>";
        results_table_html += "<thead><tr><th>Name</th><th>Nationality</th><th>Team Name</th><th>Position</th><th>Age</th></tr></thead><tbody>";
        for(let i = 0; i < response.length; i += 1) {
            results_table_html += "<tr>";
            for(let j = 0; j < response[i].length; j += 1) {   
                results_table_html += "<td>" + response[i][j] + "</td>";
            }
            results_table_html += "</tr>";
        }
        results_table_html += "</tbody></table>";
        results_table_area.innerHTML = results_table_html;
    });
    request.fail(function(jqXHR, textStatus, errorThrown) {
        console.error(errorThrown);
    });
}
function selectOrUnselectAll(elem, class_identifier) {
    let checkboxes_to_change = document.getElementsByClassName(class_identifier);
    for(let i = 0; i < checkboxes_to_change.length; i += 1) {  
        checkboxes_to_change[i].checked = elem.checked;
    }
}
function getAttributesToConsider() {
    let attributes_to_consider = Array();
    let checkboxes_for_attributes = document.getElementsByClassName("attribute");
    for(let i = 0; i < checkboxes_for_attributes.length; i += 1) {
        if(checkboxes_for_attributes[i].tagName.toUpperCase() === "INPUT" && checkboxes_for_attributes[i].checked) {
            attributes_to_consider.push(checkboxes_for_attributes[i].value);
        }
    }
    return attributes_to_consider;
}
function getTeamsToConsider() {
    let teams_to_consider = Array();
    let checkboxes_for_teams = document.getElementsByClassName("team");
    for(let i = 0; i < checkboxes_for_teams.length; i += 1) {
        if(checkboxes_for_teams[i].tagName.toUpperCase() === "INPUT" && checkboxes_for_teams[i].checked) {
            teams_to_consider.push(checkboxes_for_teams[i].value);
        }
    }
    return teams_to_consider;
}
function getPositionsToConsider() {
    let positions_to_consider = Array();
    let checkboxes_for_positions = document.getElementsByClassName("position");
    for(let i = 0; i < checkboxes_for_positions.length; i += 1) {
        if(checkboxes_for_positions[i].tagName.toUpperCase() === "INPUT" && checkboxes_for_positions[i].checked) {
            positions_to_consider.push(checkboxes_for_positions[i].value);
        }
    }
    return positions_to_consider;
}
function getMinAge() {
    let min_age_selector = document.getElementById("min_age_selector");
    return parseInt(min_age_selector.value);
}
function getMaxAge() {
    let max_age_selector = document.getElementById("max_age_selector");
    return parseInt(max_age_selector.value);
}
function getK() {
    let k_selector = document.getElementById("k_dropdown");
    return parseInt(k_selector.value);
}
function getPlayerName() {
    let search_box = document.getElementById("search_box");
    return search_box.value;
}
function validateInput(player_name, attributes_to_consider, teams_to_consider, positions_to_consider) {
    if(!player_name) {     
        alert("Enter a name");
        return false;
    }       
    else if(attributes_to_consider.length === 0) {
        alert("Check atleast one attribute");
        return false;
    }
    else if(teams_to_consider.length === 0) {
        alert("Check atleast one team");
        return false;
    }
    else if(positions_to_consider.length === 0) {
        alert("Check atleast one position");
        return false;
    }
    else {
        return true;
    }
}
