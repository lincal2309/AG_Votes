var vote_form = $('#vote')

function create_chart() {
    // As the template can either show the result or ask user to vote,
    // we need to check if the results are shown before actually launch the dedicated function
    if ($('#myChart').length) {
        var ctx = $('#myChart');
        var prog_bar = $('#nb_votes');
        var total_votes = 0;
        var nb_votes = 0;
        var quorum = 0.5;
        var labels = [];
        var values = [];
        var backgroundColor = [];
        var borderColor = [];

        $.ajax({
            // Ajax request to look for new data
            method: "GET",
            url: ctx.attr("url-endpoint"),
            data: {event_slug: ctx.attr("event-slug"), question_no: ctx.attr("question-no")},
            success: function(data) {
                total_votes = data.total_votes;
                nb_votes = data.nb_votes;

                // Sets the max value for progress bar
                prog_bar.attr("aria-valuemax", total_votes);

                // If nb votes > quorum (min nb votes for the results to be valid)
                // then displays the progress bar in green (orange by default)
                if (nb_votes / total_votes > quorum) {
                    prog_bar.removeClass("bg-warning").addClass("bg-success");
                }

                // change chart and progress bar display only if changes occurred
                if (prog_bar.attr("aria-valuenow") !== String(nb_votes)) {
                    prog_bar.attr("aria-valuenow", nb_votes);
                    display_prog = `${nb_votes} / ${total_votes}`;
                    prog_bar.text(display_prog);
                    progress = (nb_votes / total_votes) * 100;
                    display_width = `width: ${progress}%`;
                    prog_bar.attr("style", display_width);

                    labels = data.labels;
                    values = data.values;
                    backgroundColor = data.backgroundColor;
                    borderColor = data.borderColor;
            
                    setChart();
        
                }
            },
            error: function(error_data){
                console.log("error");
                console.log(error_data);
            }
        })
    
        function setChart(){
            // Design standard chart.js chart
            var myChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '# of Votes',
                        data: values,
                        backgroundColor: backgroundColor,
                        borderColor: borderColor,
                        hoverBackgroundColor: borderColor,
                        borderWidth: 1
                    }]
                },
                options: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    },
                    title: {
                        display: true,
                        text: 'Nombre de votes'
                    }
                }
            });
        }
    }
}

$(document).ready(function(event) {
    create_chart();
})


// Toggle button management
// Activate or deactivate auto-refresh
$('#switch').on("mousedown", function (e) {
    if ($(this).hasClass("unactive")) {
        // Activate auto-refresh
        // At regular interval, launch request to get new data
        $(this).removeClass("unactive").addClass("active");
        IntervalID = setInterval(create_chart, 2000);
        $(this).attr('inter-id', IntervalID)
    }
    else {
        // Unactivate auto-refresh - Stop regular request
        $(this).removeClass("active").addClass("unactive");
        IntervalID = $(this).attr('inter-id');
        clearInterval(IntervalID);
    }
})


// Enable Django CSRF-ready AJAX Calls
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});



// Catch user_choice
var choices = $('[name="choice"]')
var user_vote = 0
for (var i = 0; i < choices.length; i++) {
    choices[i].addEventListener("change", function (e) {
        user_vote = e.target.value;
    })
}

// Ajax POST request to send data
vote_form.on("submit", function(event) {
    event.preventDefault();
    if (user_vote > 0) {
        post_url = vote_form.attr('data-url');
        data = {choice: user_vote, event: vote_form.attr('data-event'), question: vote_form.attr('data-question')}
        $.ajax({
            method: "POST",
            url: post_url,
            data: data,
            success: handleSuccess,
            error: handleError,
        })
    }

    function handleSuccess(data, textStatus, jqXHR){
        user_vote = 0;
        $('[name="choice"]').attr('disabled', true);
        $('#submit-btn').attr('disabled', true);
        $('#submit-btn').removeClass('btn-success').addClass('btn-grey');
        $('#next-btn').removeClass('disabled')
        $('#voteOK').modal();
    }

    function handleError(jqXHR, textStatus, errorThrown){
        console.log(jqXHR);
        console.log(textStatus);
        console.log(errorThrown);
    }
})