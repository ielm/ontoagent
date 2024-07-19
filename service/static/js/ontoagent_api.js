
function apiGetFrame(id, callback) {
    $.ajax({
        url: "/api/frame?id=" + encodeURIComponent(id),
        method: "GET",
    }).done(function(data) {
        var output = JSON.parse(data);
        callback(output);
    }).fail(function(error) {
        console.log(error);
    });
}

function apiGetImpasse(id, callback) {
    $.ajax({
        url: "/api/impasse?id=" + id,
        method: "GET",
    }).done(function(data) {
        var output = JSON.parse(data);
        callback(output);
    }).fail(function(error) {
        console.log(error);
    });
}

function apiGetSignals(status, callback) {
    $.ajax({
        url: "/api/signals?status=" + status,
        method: "GET",
    }).done(function(data) {
        var output = JSON.parse(data);
        callback(output);
    }).fail(function(error) {
        console.log(error);
    });
}

function apiGetReport(id, callback) {
    $.ajax({
        url: "/api/report?id=" + id,
        method: "GET",
    }).done(function(data) {
        var output = JSON.parse(data);
        callback(output);
    }).fail(function(error) {
        console.log(error);
    });
}

function apiGetSignal(id, callback) {
    $.ajax({
        url: "/api/signal?id=" + id,
        method: "GET",
    }).done(function(data) {
        var output = JSON.parse(data);
        callback(output);
    }).fail(function(error) {
        console.log(error);
    });
}

function apiReleaseEffector(id, callback) {
    var data = {
        "effector": id
    };

    $.ajax({
        url: "/signal/release",
        type: "POST",
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        dataType: "json"
    }).done(function(data) {
        var output = JSON.parse(data);
        callback(output);
    }).fail(function(error) {
        console.log(error);
    });
}

function apiSignalSpeech(text, speaker, callback) {
    var data = {
        "speaker": speaker,
        "text": text
    };

    $.ajax({
        url: "/signal/speech",
        type: "POST",
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        dataType: "json"
    }).done(function(data) {
        callback(data);
    }).fail(function(error) {
        console.log(error);
    });
}

function apiLoadKnowledgeFile(package, file, callback) {
    var data = {
        "package": package,
        "file": file
    };

    $.ajax({
        url: "/ontolang/load",
        type: "POST",
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        dataType: "json"
    }).done(function(data) {
        callback(data);
    }).fail(function(error) {
        console.log(error);
    });
}

function apiExecuteOntoLang(ontolang, callback) {
    var data = {
        "ontolang": ontolang
    };

    $.ajax({
        url: "/ontolang/execute",
        type: "POST",
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        dataType: "json"
    }).done(function(data) {
        callback(data);
    }).fail(function(error) {
        console.log(error);
    });
}

// Demo methods are outside of the normal API; these are for forcing certain situations in a demo / debug setting.

function demoAgendaAddGoal(definition, variables, subgoal_of, callback) {
    var data = {
        "definition": definition,
        "variables": variables,
        "subgoal_of": subgoal_of,
    };

    $.ajax({
        url: "/demo/agenda/add_goal",
        type: "POST",
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        dataType: "json"
    }).done(function(data) {
        callback(data);
    }).fail(function(error) {
        console.log(error);
    });
}