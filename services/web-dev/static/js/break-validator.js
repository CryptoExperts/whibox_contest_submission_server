(function(crx_wb, undefined) {

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

    crx_wb.prikeyChanged = function(element) {
        if (element.value.length == 0) {
            crx_wb.disableButton();
            document.getElementById('prikey-ko').textContent = ' ';
            document.getElementById('prikey-form-group').classList.remove('has-warning');
        } else {
            var re = /^[0-9a-fA-F]{64}$/;
            if (element.value.match(re)) {
                crx_wb.enableButton();
                document.getElementById('prikey-ko').textContent = ' ';
                document.getElementById('prikey-form-group').classList.remove('has-warning');
            } else {
                crx_wb.disableButton();
                document.getElementById('prikey-ko').textContent = 'This key should be a string of 64 hexadecimal digits';
                document.getElementById('prikey-form-group').classList.add('has-warning');
            }
        }
    }

}(window.crx_wb = window.crx_wb || {}));
