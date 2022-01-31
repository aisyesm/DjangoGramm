"use strict"


document.addEventListener("DOMContentLoaded", function() {
    let liked = JSON.parse(document.getElementById('liked').textContent)
    const postId = JSON.parse(document.getElementById('postId').textContent)
    const userId = JSON.parse(document.getElementById('userId').textContent)
    const heart = document.getElementById('heart')
    const i = heart.getElementsByTagName('i')[0]
    setHeart(i, liked)

    const numLikes = document.getElementById('num-likes')
    const likeWord = document.getElementById('like-word')
    heart.addEventListener('click', () => {
        liked = !liked
        if (!liked) {
            fetch(`${window.location.origin}/app/likes/${postId}/${userId}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                })
                .then(response => {
                    if (response.ok) {
                        setHeart(i, liked)
                        adjustNumLikes(numLikes, likeWord, -1)
                    }
                    else {
                        alert(`You request cannot be proceeded (error code ${response.status}), please reload the page`)
                    }
                })
                .catch((error) => {
                  alert(`There has been a problem with your fetch operation: ${error}`)
                });
        }
        else {
            fetch(`${window.location.origin}/app/likes/${postId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: JSON.stringify({'user_id': userId}),
                })
                .then(response => {
                    if (response.ok) {
                        setHeart(i, liked)
                        adjustNumLikes(numLikes, likeWord, 1)
                    }
                    else {
                        alert(`You request cannot be proceeded (error code ${response.status}), please reload the page`)
                    }
                })
                .catch((error) => {
                  alert(`There has been a problem with your fetch operation: ${error}`)
                });
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

function getCookie(name) {
    let cookieValue = null
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';')
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim()
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
                break
            }
        }
    }
    return cookieValue
}