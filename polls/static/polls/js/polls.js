// =====================================
//           GLOBAL FUNCTIONS
// =====================================

// Display page management
$(document).ready(function() {
    if ($('#results').length > 0) {
        // == At startup, checks context to personalize display ==

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
    };

    if ($('#admin-polls').length > 0) {
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
            case 4:
                adminOptions()
                break;
            default:
                adminEvents()
        }

        if ($('#display_msg').length > 0) {
            $('#display_msg').modal('show');
        }

    };

    if ($('select').length > 0) {
        // Unselect any choice within a "select multiple" box
        $('select').removeAttr('required');
        $('select option').removeAttr('selected');
    };

    if ($('#admin-options').length > 0) {
        // For admin options, enable or disable options according to displayed values
        if ($('#id_use_groups').prop('checked')) {
            $('#id_rule').prop('disabled', false)
            $('#id_upd_rule').prop('disabled', false)
        } else {
            $('#id_rule').prop('disabled', true)
            $('#id_upd_rule').prop('disabled', true)
        }

        // Hide mail server password
        $('#id_fax').attr('type', 'password');

        $('#toggle_mail_mdp').on('click', function() {
            if ($('#id_fax').attr('type') === 'password') {
                $('#id_fax').attr('type', '');
                $('#toggle_mail_mdp span').attr('title', 'Masquer').attr('data-original-title', '')
                var text = $('#toggle_mail_mdp').html()
                $('#toggle_mail_mdp').html(text.replace('Voir', 'Masquer'))
            } else {
                $('#id_fax').attr('type', 'password');
                $('#toggle_mail_mdp span').attr('title', 'Afficher').attr('data-original-title', '')
                var text = $('#toggle_mail_mdp').html()
                $('#toggle_mail_mdp').html(text.replace('Masquer', 'Voir'))
            }
        })
    }

    // Close modals on cancel button
    // As far as only 1 modal can be displayed : all modals can be closed, so we can use the 'modal' class
    $('.close-btn').on('click', function () {
        $('.modal').modal('hide');
    })


    // Tooltips
    $(document).ready(function(){
        $('[data-toggle="tooltip"]').tooltip();
    });


    // Go back to previous page
    $('.back_btn').on('click', function(event) {
        event.preventDefault();
        history.back();
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


    // =====================================
    //      EVENTS MANAGEMENT FUNCTIONS
    // =====================================

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


    // =====================================
    //     VOTES MANAGEMENT FUNCTIONS
    // =====================================

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


    // =====================================
    //      PROXY BUTTONS
    // =====================================

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


    // =====================================
    //      Administration functions
    // =====================================

    // Manage admin menu display according to the active page
    function adminEvents() {
        $('#menu-events').addClass("underlined");
        $('#menu-users').removeClass("underlined");
        $('#menu-groups').removeClass("underlined");
        $('#menu-options').removeClass("underlined");
    }

    function adminUsers() {
        $('#menu-events').removeClass("underlined");
        $('#menu-users').addClass("underlined");
        $('#menu-groups').removeClass("underlined");
        $('#menu-options').removeClass("underlined");
    }

    function adminGroups() {
        $('#menu-events').removeClass("underlined");
        $('#menu-users').removeClass("underlined");
        $('#menu-groups').addClass("underlined");
        $('#menu-options').removeClass("underlined");
    }

    function adminOptions() {
        $('#menu-events').removeClass("underlined");
        $('#menu-users').removeClass("underlined");
        $('#menu-groups').removeClass("underlined");
        $('#menu-options').addClass("underlined");
    }


    // Multiple select box management

    // Sort list function
    function sortlist(mylist) {
        // let lb = $(mylist);
        let elts = $(mylist).children('option');

        elts.sort(function(a,b) {
            if (a.text > b.text) return 1;
            if (a.text < b.text) return -1;
            return 0;
        })

        $(mylist).empty().append( elts );

        // arrTexts = new Array();
        
        // for(i=0; i<lb.length; i++)  {
        //     arrTexts[i] = lb.options[i].text;
        // }
        
        // arrTexts.sort();
        
        // for(i=0; i<lb.length; i++)  {
        //     lb.options[i].text = arrTexts[i];
        //     lb.options[i].value = arrTexts[i];
        // }
    }

    // Send an value from a select box to another
    function add_option(source, dest, elt) {
        let new_option = new Option(elt.text(), elt.val())
        $(dest).append(new_option);
        elt.remove();
        $(new_option).attr("selected", "selected");
        $(new_option).attr("has_changed", "True");

        sortlist(dest);
    }

    // Add all (from source to destination)
    $('#add_all').on("click", function(e) {
        e.preventDefault();
        $('#id_users').find('option').removeAttr('selected');
        $('#id_all_users option').each(function() {
            add_option('#id_all_users', '#id_users', $(this));
            $('#id_users_in_group').val($('#id_users_in_group').val() + "-" + String($(this).val()))
        })
    })

    // Add selected (from source to destination)
    $('#add_selected').on("click", function(e) {
        e.preventDefault();
        $('#id_users').find('option').removeAttr('selected');
        let values = $('#id_all_users').val();

        $('#id_all_users option').each(function() {
            if ( values.includes( $(this).val() ) ) {
                add_option('#id_all_users', '#id_users', $(this));
                $('#id_users_in_group').val($('#id_users_in_group').val() + "-" + String($(this).val()))
            }
        })
    })

    // Add selected by double click
    $("#id_all_users option").dblclick(function(e) {
        e.preventDefault();
        $('#id_users').find('option').removeAttr('selected');
        add_option('#id_all_users', '#id_users', $(this));
        $('#id_users_in_group').val($('#id_users_in_group').val() + "-" + String($(this).val()))
    })

    // Remove all (empty list, back to global list)
    $('#remove_all').on("click", function(e) {
        e.preventDefault();
        $('#id_all_users').find('option').removeAttr('selected');
        $('#id_users option').each(function() {
            add_option('#id_users', '#id_all_users', $(this));
            $('#id_users_in_group').val($('#id_users_in_group').val().replace(String($(this).val()), ""))
        })
    })

    // Remove selected (from source to destination)
    $('#remove_selected').on("click", function(e) {
        e.preventDefault();
        $('#id_all_users').find('option').removeAttr('selected');
        let values = $('#id_users').val();

        $('#id_users option').each(function() {
            if ( values.includes( $(this).val() ) ) {
                add_option('#id_users', '#id_all_users', $(this));
                $('#id_users_in_group').val($('#id_users_in_group').val().replace(String($(this).val()), ""))
            }
        })
    })

    // Remove selected by double click
    $("#id_users option").dblclick(function(e) {
        e.preventDefault();
        $('#id_all_users').find('option').removeAttr('selected');
        add_option('#id_users', '#id_all_users', $(this));
        $('#id_users_in_group').val($('#id_users_in_group').val().replace(String($(this).val()), ""))
    })



    // Add a question in question formset
    $('#add_question').click(function(e) {
        e.preventDefault();
        var question_idx = $('#id_question-TOTAL_FORMS').val();
        $('#question_set').append($('#question_empty_form').html().replace(/__prefix__/g, question_idx));
        $('#id_question-TOTAL_FORMS').val(parseInt(question_idx) + 1);
    });


    // Add a choice in choice formset
    $('#add_choice').click(function(e) {
        e.preventDefault();
        var choice_idx = $('#id_choice-TOTAL_FORMS').val();
        $('#choice_set').append($('#choice_empty_form').html().replace(/__prefix__/g, choice_idx));
        $('#id_choice-TOTAL_FORMS').val(parseInt(choice_idx) + 1);
    });


    // On submit, select all elements to ensure they are sent to the view
    // $('#upd_grp').on("click", function() {
    //     $('#id_all_users option').removeAttr('selected');
    //     $('#id_all_users option').each(function() {
    //         if ($(this).attr('has_changed') && $(this).attr('has_changed') == "True" ) {
    //             $(this).attr('selected', 'selected');
    //         }
    //     });

    //     console.log("Group users")
    //     $('#id_users option').attr('selected', 'selected');
    //     $('#id_users option').each(function() {
    //         if ($(this).attr('has_changed') && $(this).attr('has_changed') == "True" ) {
    //             // $(this).attr('selected', 'selected');
    //         }
    //     })
    // })


    // Expand / Collapse blocks
    $('.collapse-group').on("click", function(e) {
        e.preventDefault();
        if ($(this).hasClass("expand-group")) {
            $('.grp-content').removeClass("hidden");
            $('#btn_grp').removeClass("fa-chevron-down").addClass("fa-chevron-up");
            $(this).removeClass("expand-group").addClass("collapse-group");
        }
        else if ($(this).hasClass("collapse-group")) {
            $('.grp-content').addClass("hidden");
            $('#btn_grp').addClass("fa-chevron-down").removeClass("fa-chevron-up");
            $(this).addClass("expand-group").removeClass("collapse-group");
        }
    })

    // $('.collapse-group').on("click", function(e) {
    //     e.preventDefault();
    //     console.log("Masquer");
    //     $('.grp-content').addClass("hidden");
    //     // $('.grp-content').hide();
    //     $('#btn_grp').addClass("fa-chevron-down").removeClass("fa-chevron-up");
    //     $(this).addClass("expand-group").removeClass("collapse-group");
    // })


    // Delete user modal display
    $('.delete-user').on("click", function() {
        dlte_usr = $(this).attr("data-usr-name") + " " + $(this).attr("data-usr-first-name");
        // mdl_action = $('#form_dlt_usr').attr("action");
        $('#dlte-confirm').html("Voulez-vous supprimer l'utilisateur <strong>" + dlte_usr + "</strong> ?");
        $('#form_dlt_usr').attr("action", $('#form_dlt_usr').attr("action").replace("0", $(this).attr("data-usr-id")));
    })

    $('#close_dlte_usr').on("click", function(event) {
        event.preventDefault();
        $('#delete_usr').modal('hide');
    })



    // Delete event modal display
    $('.delete-evt').on("click", function() {
        // dlte_usr = $(this).attr("data-usr-name") + " " + $(this).attr("data-usr-first-name");
        // mdl_action = $('#form_dlt_grp').attr("action");
        $('#dlte-evt-confirm').html("Voulez-vous supprimer l'événement' <strong>" + $(this).attr("data-evt-name") + "</strong> ?");
        $('#form_dlt_evt').attr("action", $('#form_dlt_evt').attr("action").replace("0", $(this).attr("data-evt-id")));
    })

    $('#close_dlte_evt').on("click", function(event) {
        event.preventDefault();
        $('#delete_evt').modal('hide');
    })



    // Delete group modal display
    $('.delete-grp').on("click", function() {
        // dlte_usr = $(this).attr("data-usr-name") + " " + $(this).attr("data-usr-first-name");
        // mdl_action = $('#form_dlt_grp').attr("action");
        $('#dlte-grp-confirm').html("Voulez-vous supprimer le groupe <strong>" + $(this).attr("data-grp-name") + "</strong> ?");
        $('#form_dlt_grp').attr("action", $('#form_dlt_grp').attr("action").replace("0", $(this).attr("data-grp-id")));
    })

    $('#close_dlte_grp').on("click", function(event) {
        event.preventDefault();
        $('#delete_grp').modal('hide');
    })


    // Enable or disable options according to users's choice to use groups or not
    $('#id_use_groups').on("change", function() {
        if (this.checked) {
            $('#id_rule').prop('disabled', false)
            $('#id_upd_rule').prop('disabled', false)
        } else {
            $('#id_rule').prop('disabled', true)
            $('#id_upd_rule').prop('disabled', true)
        }
    })
})
