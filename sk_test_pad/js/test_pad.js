$(document).ready(function() {
	var hup = "hang_up";
	var pup = "pick_up";

	$("#mp_receiver")
		.html(pup)
		.click(function() {
			if($(this).html() == hup) {
				next_state = pup;
			} else if($(this).html() == pup) {
				next_state = hup;
			}

			$.ajax({
				url : $(this).html(),
				context : this
			}).done(function(json) {
				console.info(json);				
				$(this).html(next_state);
			});
		});

	$("#mp_only_press")
		.click(function() {
			$.ajax({
				url : "/mapping/3"
			}).done(function(json) {
				console.info(json);
			})
		});
});