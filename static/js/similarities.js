$(document).ready(function () {
    $("#searchBox").selectize({
        sortField: "text"
    });
});
function findSimilarities() {
    let playerName = getPlayerName();
    let attributesToConsider = getAttributesToConsider();
    let teamsToConsider = getTeamsToConsider();
    let positionsToConsider = getPositionsToConsider();
    let minAge = getMinAge();
    let maxAge = getMaxAge();
    let k = getK();
    if (!validateInput(playerName, attributesToConsider, teamsToConsider, positionsToConsider)) {
        return;
    }
    if (maxAge < minAge) {
        let t = maxAge;
        maxAge = minAge;
        minAge = t;
    }
    let request = $.ajax({
        url: "/findSimilarities",
        type: "post",
        data: {
            "playerName": playerName,
            "attributesToConsider": JSON.stringify(attributesToConsider),
            "teamsToConsider": JSON.stringify(teamsToConsider),
            "positionsToConsider": JSON.stringify(positionsToConsider),
            "minAge": minAge,
            "maxAge": maxAge,
            "k": k
        }
    });
    request.done(function (response, textStatus, XHR) {
        response = JSON.parse(response);
        console.log(response);
        let resultsTableArea = document.getElementById("resultsTableArea");
        resultsTableHtml = "<table id='resultsTable' border='1'>";
        resultsTableHtml += "<thead><tr><th>Name</th><th>Nationality</th><th>Team Name</th><th>Position</th><th>Age</th></tr></thead><tbody>";
        for (let i = 0; i < response.length; i += 1) {
            resultsTableHtml += "<tr>";
            for (let j = 0; j < response[i].length; j += 1) {
                resultsTableHtml += "<td>" + response[i][j] + "</td>";
            }
            resultsTableHtml += "</tr>";
        }
        resultsTableHtml += "</tbody></table>";
        resultsTableArea.innerHTML = resultsTableHtml;
    });
    request.fail(function (jqXHR, textStatus, errorThrown) {
        console.error(errorThrown);
    });
}
function selectOrUnselectAll(elem, classIdentifier) {
    let checkboxesToChange = document.getElementsByClassName(classIdentifier);
    for (let i = 0; i < checkboxesToChange.length; i += 1) {
        checkboxesToChange[i].checked = elem.checked;
    }
}
function getAttributesToConsider() {
    let attributesToConsider = Array();
    let checkboxesForAttributes = document.getElementsByClassName("attribute");
    for (let i = 0; i < checkboxesForAttributes.length; i += 1) {
        if (checkboxesForAttributes[i].tagName.toUpperCase() === "INPUT" && checkboxesForAttributes[i].checked) {
            attributesToConsider.push(checkboxesForAttributes[i].value);
        }
    }
    return attributesToConsider;
}
function getTeamsToConsider() {
    let teamsToConsider = Array();
    let checkboxesForTeams = document.getElementsByClassName("team");
    for (let i = 0; i < checkboxesForTeams.length; i += 1) {
        if (checkboxesForTeams[i].tagName.toUpperCase() === "INPUT" && checkboxesForTeams[i].checked) {
            teamsToConsider.push(checkboxesForTeams[i].value);
        }
    }
    return teamsToConsider;
}
function getPositionsToConsider() {
    let positionsToConsider = Array();
    let checkboxesForPositions = document.getElementsByClassName("position");
    for (let i = 0; i < checkboxesForPositions.length; i += 1) {
        if (checkboxesForPositions[i].tagName.toUpperCase() === "INPUT" && checkboxesForPositions[i].checked) {
            positionsToConsider.push(checkboxesForPositions[i].value);
        }
    }
    return positionsToConsider;
}
function getMinAge() {
    let minAgeSelector = document.getElementById("minAgeSelector");
    return parseInt(minAgeSelector.value);
}
function getMaxAge() {
    let maxAgeSelector = document.getElementById("maxAgeSelector");
    return parseInt(maxAgeSelector.value);
}
function getK() {
    let kSelector = document.getElementById("kDropdown");
    return parseInt(kSelector.value);
}
function getPlayerName() {
    let searchBox = document.getElementById("searchBox");
    return searchBox.value;
}
function validateInput(playerName, attributesToConsider, teamsToConsider, positionsToConsider) {
    if (!playerName) {
        alert("Enter a name");
        return false;
    }
    else if (attributesToConsider.length === 0) {
        alert("Check atleast one attribute");
        return false;
    }
    else if (teamsToConsider.length === 0) {
        alert("Check atleast one team");
        return false;
    }
    else if (positionsToConsider.length === 0) {
        alert("Check atleast one position");
        return false;
    }
    else {
        return true;
    }
}
