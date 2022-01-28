"use strict"


document.addEventListener("DOMContentLoaded", function() {
    console.log('js loaded')
    const liked = JSON.parse(document.getElementById('liked').textContent)
    const i = document.getElementById('id-heart')
    setHeart(i, liked)

})


function setHeart (i, liked) {
    if (!liked) {
        i.className = 'far fa-heart'
    }
    else {
        i.className = 'fas fa-heart red-heart'
    }
}