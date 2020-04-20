
// Charts creation
function create_chart() {
    // As the template can either show the result or ask user to vote,
    // we need to check if the results are shown before actually launch the dedicated function
    if ($('#global_chart').length) {
        var ctx = $('#global_chart');
        var prog_bar = $('#global_nb_votes');
        var total_votes = 0;
        var nb_votes = 0;
        var quorum = parseInt($('#quorum').attr("data-quorum")) / 100;
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
                charts_data = data.chart_data['global'];
                nb_charts = data.nb_charts;

                backgroundColor = data.backgroundColor;
                borderColor = data.borderColor;


                // Global results chart
                setChartData();

                // Group results charts
                for (var i = 1; i <= nb_charts; i++) {
                    ctx = $(`#chart${i}`);
                    prog_bar = $(`#nb_votes${i}`);

                    charts_data = data.chart_data[`chart${i}`];

                    setChartData();

                }
            },
            error: function(error_data){
                console.log("error");
                console.log(error_data);
            }
        })
    
        function setChartData() {
            total_votes = charts_data['total_votes'];
            nb_votes = charts_data['nb_votes'];

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

                labels = charts_data['labels'];
                values = charts_data['values'];
        
                setChart();
            }
        
        }
        
        
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

// Display page management
$(document).ready(function(event) {
    if ($('#results').length > 0) {
        // Results page : create charts if data available
        let nb_charts = $('#nb_questions').attr('data-nb');
        for (let chart_num = 1; chart_num <= nb_charts; chart_num++) {
            let data = JSON.parse(document.getElementById(`${chart_num}`).textContent);
            let ctx = $(`#chart${chart_num}`);
            let charts_data = data.chart_data;

            backgroundColor = data.backgroundColor;
            borderColor = data.borderColor;

            labels = charts_data['labels'];
            values = charts_data['values'];

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
                        display: false,
                        text: 'Nombre de votes'
                    }
                }
            });


        }
        
    }

    else if ($('#admin-polls').length > 0) {
        // Admin page : show admin events options
        switch(parseInt($("#menu_id").val())) {
            case 1:
                adminEvents()
                break;
            case 2:
                adminUsers()
                break;
            case 3:
                adminGroups()
                break;
            default:
                adminEvents()
        }

        if ($('#display_msg').length > 0) {
            $('#display_msg').modal('show');
        }

    }

})

// Close modals on cancel button
// As far as only 1 modal can be displayed : all modals can be closed, so we can use the 'modal' class
$('.close-btn').on('click', function () {
    $('.modal').modal('hide');
})


// Toggle button management
// Activate or deactivate auto-refresh
$('#switch').on("mousedown", function (e) {
    if ($(this).hasClass("unactive")) {
        // Activate auto-refresh
        // At regular interval, launch request to get new data
        $(this).removeClass("unactive").addClass("active");
        IntervalID = setInterval(create_chart, 5000);
        $(this).attr('inter-id', IntervalID)
    }
    else {
        // Unactivate auto-refresh - Stop regular request
        $(this).removeClass("active").addClass("unactive");
        IntervalID = $(this).attr('inter-id');
        clearInterval(IntervalID);
    }
})


// Tooltips
$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
  });


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


// ==========================
//      Vote management
// ==========================

var vote_form = $('#vote')
// Ajax POST request to send user's vote choice
vote_form.on("submit", function(event) {
    event.preventDefault();
    let user_vote = $('[name="choice"]:checked').val();
    // Data sent only if user actually voted 
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

    function handleSuccess(data){
        // Reinitialize data and set buttons's status accordingly
        user_vote = data.nb_votes;
        if (user_vote > 0) {
            $('[name="choice"]').prop('checked', false);
            if (user_vote > 1) {
                $('#nb_votes').text("Vous disposez de " + user_vote + " votes");
            }
            else {
                $('#nb_votes').text("Vous disposez de 1 vote");
            }
        }
        else {
            $('#nb_votes').remove();
            $('#nb_proc').remove();
            $('[name="choice"]').prop('checked', false).attr('disabled', true);
            $('#submit-btn').attr('disabled', true);
            $('#submit-btn').removeClass('btn-success').addClass('btn-grey');
            $('#next-btn').removeClass('disabled');
        }
        $('#voteOK').modal();
    }

    function handleError(jqXHR, textStatus, errorThrown){
        console.log(jqXHR);
        console.log(textStatus);
        console.log(errorThrown);
    }
})


// ==========================
//  Proxy buttons management
// ==========================

// User gives proxy
var proxy_form = $('#proxy')

proxy_form.on("submit", function(event) {
    event.preventDefault();
    let proxy_choice = $('[name="proxy"]:checked').val()
    if (proxy_choice > 0) {
        post_url = proxy_form.attr('data-url');
        data = {user: proxy_form.attr('data-user'), event_slug: proxy_form.attr('data-event'), proxy: proxy_choice};
        $.ajax({
            method: "POST",
            url: post_url,
            data: data,
            success: handleSuccess,
            error: handleError,
        });
    }

    function handleSuccess(data, textStatus, jqXHR){
        // Reinitialize data and set buttons's status accordingly
        first_name = data.proxy_f_name;
        last_name = data.proxy_l_name;
        proxy_id = data.proxy;

        let text_elt = "<p class=\"mt-4 pl-2 text-center\">Vous avez donné pouvoir à : <strong>" + first_name + " " + last_name + "</strong></p>"
        $('#Pouvoirs').append(text_elt);
        $('.proxy_list').remove();

        $('#Pouvoirs').append('<div class="text-center" id="pwr"></div>');
        $('#pwr').append('<input type="text" name="Action" value="Cancel" hidden>')
        $('#pwr').append('<input type="text" name="event" value="{{ event.slug }}" hidden>')
        $('#pwr').append("<button id='cancel_proxy'></button>")
        $('#cancel_proxy').addClass("btn btn-secondary mt-4").attr("type", "submit").attr("data-user", proxy_id).html('Annuler le pouvoir');

    }

    function handleError(jqXHR, textStatus, errorThrown){
        console.log(jqXHR);
        console.log(textStatus);
        console.log(errorThrown);
    }

})

// Accept proxy

$('#accept_proxy').on("click", function(event) {
    event.preventDefault();
    let user_proxy_form = document.querySelector('#user_proxy')
    let proxies = [];
    let choices = [];

    for (let i = 0; i < user_proxy_form.elements.length; i++) {
        if (user_proxy_form.elements[i].checked) {
            // Build a table with proxy_ids (to send to the server and update db)
            // and element id to update display afterwards
            proxies.push(user_proxy_form.elements[i]['value']);
            choices.push(user_proxy_form.elements[i]['id']);
        }
    }

    if (proxies.length > 0) {
        let usr_proxy_form = $('#user_proxy')
        post_url = usr_proxy_form.attr('data-url');
        // proxy list needs to be converted to JSON to be sent properly
        data = {user: usr_proxy_form.attr('data-user'), event_slug: usr_proxy_form.attr('data-event'), cancel_list: JSON.stringify(proxies)};
        $.ajax({
            method: "POST",
            url: post_url,
            data: data,
            success: handleSuccess,
            error: handleError,
        });
    }
    
    function handleSuccess() {
        for (let i = 0; i < choices.length; i++) {
            $(`[for=${choices[i]}]`).addClass('checkmark');
            $(`[id=${choices[i]}]`).prop('checked', false);
        }
    }

    function handleError(jqXHR, textStatus, errorThrown){
        console.log(jqXHR);
        console.log(textStatus);
        console.log(errorThrown);
    }

})

$('#refuse_proxy').on("click", function(event) {
    console.log("Refus proxy");
    if ($('[name="user_proxy"]:checked').length === 0) {
        console.log("Rien n'est sélectionné");
        event.preventDefault();
    }
})

$('#cancel_proxy').on("click", function(event) {
    console.log("Annulation proxy");
})


// ==================================
//      Administration functions
// ==================================

function adminEvents() {
    $('#menu-events').addClass("underlined");
    $('#menu-users').removeClass("underlined");
    $('#menu-groups').removeClass("underlined");
}

function adminUsers() {
    $('#menu-events').removeClass("underlined");
    $('#menu-users').addClass("underlined");
    $('#menu-groups').removeClass("underlined");
}

function adminGroups() {
    $('#menu-events').removeClass("underlined");
    $('#menu-users').removeClass("underlined");
    $('#menu-groups').addClass("underlined");
}

// Delete user modal display
$('.delete-user').on("click", function() {
    dlte_usr = $(this).attr("data-usr-name") + " " + $(this).attr("data-usr-first-name");
    mdl_action = $('#form_dlt_usr').attr("action");
    $('#dlte-confirm').html("Voulez-vous supprimer l'utilisateur <strong>" + dlte_usr + "</strong> ?");
    $('#form_dlt_usr').attr("action", $('#form_dlt_usr').attr("action").replace("0", $(this).attr("data-usr-id")));
})

// ==========================
//     Various functions
// ==========================

// Go back to previous page
$('.back_btn').on('click', function(event) {
    event.preventDefault();
    history.back();
});
