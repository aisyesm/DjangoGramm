"use strict"


document.addEventListener("DOMContentLoaded", function() {
    let liked = JSON.parse(document.getElementById('liked').textContent)
    const heart = document.getElementById('heart')
    const i = heart.getElementsByTagName('i')[0]
    setHeart(i, liked)

    const numLikes = document.getElementById('num-likes')
    const likeWord = document.getElementById('like-word')
    heart.addEventListener('click', () => {
        liked = !liked
        setHeart(i, liked)
        if (liked) {
            adjustNumLikes(numLikes, likeWord, 1)
        }
        else {
            adjustNumLikes(numLikes, likeWord, -1)
        }
    })
})


function setHeart (i, liked) {
    if (!liked) {
        i.className = 'far fa-heart'
    }
    else {
        i.className = 'fas fa-heart red-heart'
    }
}

function adjustNumLikes(numLikes, likeWord, delta) {
    let num = numLikes.textContent
    num = parseInt(num, 10)
    num += delta
    numLikes.textContent = num
    if (num === 1) {
        likeWord.textContent = 'like'
    }
    else {
        likeWord.textContent = 'likes'
    }
}