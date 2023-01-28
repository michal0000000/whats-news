function changeBiasedMode(unbiased){

    var searchParams = new URLSearchParams(window.location.search);
    
    // If currently unbiased, changed to biased
    if (unbiased == true) {
        //window.location.href = "?u=false";
        searchParams.set('u','false');

    // If currently biased, changed to unbiased
    } else {
        //window.location.href = "?u=true";
        searchParams.set('u','true');
    }

    window.location.href = '?' + searchParams.toString()
}