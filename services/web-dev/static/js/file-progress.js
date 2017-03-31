(function(crx_wb, undefined) {

    /* Very useful: http://stackoverflow.com/questions/10956574/why-might-xmlhttprequest-progressevent-lengthcomputable-be-false */
    /* http://www.matlus.com/html5-file-upload-with-progress/ */

    crx_wb.uploadProgress = function(evt) {
	crx_wb.disableButton();
	document.getElementById('progress-bar-div').style.visibility = 'visible';
	progressBar = document.getElementById('progress-bar');
	progressBarSpan = document.getElementById('progress-bar-span');
	if (evt.lengthComputable) {
	    var percentComplete = Math.round(evt.loaded * 100 / evt.total);
	    console.log('percentComplete: ', percentComplete);
	    progressBar.style.width = percentComplete.toString() + '%';
	    progressBarSpan.textContent = percentComplete + '% Complete';
	}
	else {
	    progressBar.style.width = '100%';
	}
    }

    crx_wb.uploadComplete = function(evt) {
	/* This event is raised when the server send back a response */
	if (evt.target.status >= 400) {
	    document.open();
	    document.write(evt.target.response);
	    document.close();
	} else {
	    progressBar = document.getElementById('progress-bar');
	    progressBarSpan = document.getElementById('progress-bar-span');
	    progressBar.style.width = '100%';
	    progressBarSpan.textContent = '100% Complete';
	    window.location.href = '/submit/candidate/ok';
	}
    }

    crx_wb.uploadFile = function(formElement) {
	console.log("Call to uploadFile")
	var xhr = new XMLHttpRequest();
	var fd = new FormData(formElement);

	/* event listeners */
	xhr.upload.addEventListener("progress", crx_wb.uploadProgress, false);
	xhr.addEventListener("load", crx_wb.uploadComplete, false);

	/* post the form */
	xhr.open("POST", "/submit/candidate");
	xhr.send(fd);
    }

    crx_wb.submit = function(formElement) {
	console.log("Form submitted, we prevent the default behavior.")
	crx_wb.uploadFile(formElement);
	return true;
    }

    document.addEventListener("DOMContentLoaded", function(event) {
	var formElement = document.getElementById('form');
	formElement.addEventListener('submit', function(event) {
	    event.preventDefault();
	    crx_wb.submit(formElement);
	})
    });


}(window.crx_wb = window.crx_wb || {}));
