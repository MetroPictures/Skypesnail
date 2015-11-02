$(document).ready(function() {
	$("#mp_only_press")
		.click(function() {
			$.ajax({
				url : "/mapping/3"
			}).done(function(json) {
				console.info(json);
			})
		});
});