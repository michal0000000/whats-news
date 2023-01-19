function changeBiasedMode(unbiased){
    
    // If currently unbiased, changed to biased
    if (unbiased == true) {
        window.location.href = "?u=false";

    // If currently biased, changed to unbiased
    } else {
        window.location.href = "?u=true";
    }
}