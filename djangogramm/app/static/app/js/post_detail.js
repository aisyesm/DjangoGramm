"use strict"


document.addEventListener("DOMContentLoaded", function() {
    console.log('js loaded')
    const liked = JSON.parse(document.getElementById('liked').textContent)
    console.log(liked)

})