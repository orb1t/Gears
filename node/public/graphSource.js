$(function() {

	$("#fetch").click(function(){
		var dataURL = "recent";

		function onDataRecieved(data){
			var temperatureSet = [];
			var pressureSet = [];

			$.each(data, function(key, value){
				temperatureSet.push([key, value.temperature]);
				pressureSet.push([key, value.pressure]);
			});
			
			$.plot("#placeholder", [
				{ data: temperatureSet, label: "Temperature (°C)" },
				{ data: pressureSet, label: "Pressure (Pa)", yaxis: 2 }
			], {
				//xaxes : [{ mode: "time"}],		//must include jquery.flot.time.min.js for this!
				yaxes : [{}, {position: "right"}]
			});

		}

		$.ajax({
			url:dataURL,
			type:"GET",
			dataType:"json",
			success:onDataRecieved
		});

	});

	// var d1 = [];
	// for (var i = 0; i < 14; i += 0.5) {
	//	d1.push([i, Math.sin(i)]);
	// }

	// var d2 = [[0, 3], [4, 8], [8, 5], [9, 13]];

	// // A null signifies separate line segments

	// var d3 = [[0, 12], [7, 12], null, [7, 2.5], [12, 2.5]];

	// $.plot("#placeholder", [ d1, d2, d3 ]);

	// Add the Flot version string to the footer

	$("#footer").prepend("Flot " + $.plot.version + " &ndash; ");
});