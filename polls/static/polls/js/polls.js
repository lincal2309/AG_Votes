// google.charts.load('current', {'packages':['corechart']});
// google.charts.setOnLoadCallback(drawChart);

// function drawChart() {
//     var nb_choices = $('#nb_choices').val();
//     var chart_data = [['Choix', 'Nb votes']];
//     console.log(chart_data);
//     for (var i = 1; i <= nb_choices; i+=2) {
//         console.log($('#chart_data>input:eq(i)').val());
//         var choix = $('#chart_data>input:eq(i)').val();
//         var votes = $('#chart_data>input:eq(i+1)').val();
//         new_val = [choix, votes];
//         console.log(new_val);
//         chart_data.push(new_val);
//         console.log(chart_data);
//     };
  
//     var data = google.visualization.arrayToDataTable(chart_data);

//   var options = {
//     title: 'My Daily Activities'
//   };

//   var chart = new google.visualization.PieChart(document.getElementById('piechart'));

//   chart.draw(data, options);
// }



