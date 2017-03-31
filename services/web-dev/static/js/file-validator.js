(function(crx_wb, undefined) {

    crx_wb.formElementsValidated = [false, false];

    crx_wb.disableButton = function() {
	button = document.getElementById('submitButton');
	button.classList.add('disabled');
	button.disabled = true;
    }

    crx_wb.enableButton = function() {
	button = document.getElementById('submitButton');
	button.classList.remove('disabled');
	button.disabled = false;
    }

    crx_wb.tryActivateButton = function() {
	for (var i = 0; i < crx_wb.formElementsValidated.length; i++) {
	    if (crx_wb.formElementsValidated[i] == false) {
		crx_wb.disableButton();
		return
	    }
	}
	crx_wb.enableButton();
    }

    document.addEventListener("DOMContentLoaded", function(event) {
	window.crx_wb.keyChanged(document.getElementById('key'))
    });

    crx_wb.bytesToSize = function(bytes) {
	var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
	if (bytes == 0) return '0 Byte';
	var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
	return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
    };


    crx_wb.fileSelected = function(element, max_content_length) {
	var file = element.files[0];
	if (file) {
	    filename = element.value.replace(/\\/g, '/').replace(/.*\//, '');
	    document.getElementById('filename').value = filename;
	    if (file.size > max_content_length) {
		document.getElementById('fileSize-ok').textContent = '';
		document.getElementById('fileSize-ko').textContent = 'Your file size is ' + crx_wb.bytesToSize(file.size) + ', which is too large.';
		crx_wb.formElementsValidated[0] = false;
	    } else {
		document.getElementById('fileSize-ok').textContent = 'Your file size is ' + crx_wb.bytesToSize(file.size) + ', perfect!';
		document.getElementById('fileSize-ko').textContent = '';
		crx_wb.formElementsValidated[0] = true;
	    }
	    crx_wb.tryActivateButton();
	} else {
	    document.getElementById('filename').textContent = '';
	}
	return false;
    }

    crx_wb.keyChanged = function(element) {
	if (element.value.length == 0) {
	    crx_wb.formElementsValidated[1] = false;
	    document.getElementById('key-ko').textContent = ' ';
	    document.getElementById('key-form-group').classList.remove('has-warning');
	} else {
	    var re = /^[0-9a-fA-F]{32}$/;
	    if (element.value.match(re)) {
		crx_wb.formElementsValidated[1] = true;
		document.getElementById('key-ko').textContent = ' ';
		document.getElementById('key-form-group').classList.remove('has-warning');
	    } else {
		crx_wb.formElementsValidated[1] = false;
		document.getElementById('key-ko').textContent = 'This key should be a string of 32 hexadecimal digits';
		document.getElementById('key-form-group').classList.add('has-warning');
	    }
	}
	crx_wb.tryActivateButton();
    }

}(window.crx_wb = window.crx_wb || {}));
