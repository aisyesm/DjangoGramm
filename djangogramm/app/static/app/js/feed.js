"use strict"

const curScriptElement = document.currentScript

document.addEventListener("DOMContentLoaded", function() {
    let start = 0
    const offset = 7
    getPosts(start, offset, true)
    const total_num_posts = curScriptElement.getAttribute('total_num_posts')

    window.addEventListener('scroll', function() {
        let windowRelativeBottom = document.documentElement.getBoundingClientRect().bottom
        if (windowRelativeBottom < document.documentElement.clientHeight + 10) {
            start += offset
            if (start < total_num_posts) {
                getPosts(start, offset)
            }
        }
    })
})

function getPosts (start, offset, firstTime=false) {
    fetch(`${window.location.origin}/app/posts?offset=${offset}&start=${start}`)
    .then (response => response.json())
    .then (json => {
        if (json.length === 0 && firstTime) {
            const el = document.createElement("div")
            el.innerHTML = "You don't follow anyone yet <br> find people in <strong>'explore'</strong> link!"
            el.style = 'text-align: center;'
            document.getElementById('content').append(el)
        }
        else {
            showPosts(json)
        }
    })
}

function showPosts (posts) {
    const container = document.querySelector('.posts')
    const authUserID = JSON.parse(document.getElementById('authUserId').textContent)
    posts.forEach(post => {
        const divPost = document.createElement('div')
        divPost.classList.add('card');
        divPost.style = 'border-radius: 10px; margin-bottom: 20px;'

        const divAuthorPost = document.createElement('div')
        divAuthorPost.classList.add('post-author')

        const divAvatar = document.createElement('div')
        divAvatar.classList.add('avatar')
        const userAvatarLink = document.createElement('a')
        userAvatarLink.href = `${window.location.origin}/app/${post.user}/profile`
        const imgAvatar = document.createElement('img')
        if (post.user_avatar) {
            imgAvatar.src = post.user_avatar
        }
        else {
            imgAvatar.src = "/static/app/img/empty_user.jpg"
        }
        userAvatarLink.append(imgAvatar)
        divAvatar.append(userAvatarLink)
        divAuthorPost.append(divAvatar)

        const divAuthor = document.createElement('div')
        divAuthor.classList.add('author')
        const userLink = document.createElement('a')
        userLink.href = `${window.location.origin}/app/${post.user}/profile`
        userLink.textContent = `${post.first_name} ${post.last_name}`
        divAuthor.append(userLink)
        divAuthorPost.append(divAuthor)

        const divPhoto = document.createElement('div')
        divPhoto.classList.add('photo')
        const imgPhoto = document.createElement('img')
        imgPhoto.src = post.image
        divPhoto.append(imgPhoto)

        const likeContainer = document.createElement('div')
        likeContainer.className = 'like-container d-flex mt-3 ms-3'
        const heart = document.createElement('div')
        heart.className = 'heart d-flex align-items-center'
        heart.id = 'heart'
        const heartSvg = document.createElement('i')
        let liked = post.likes.includes(authUserID)
        setHeart(heartSvg, liked)
        heart.appendChild(heartSvg)
        likeContainer.appendChild(heart)
        const amountContainer = document.createElement('div')
        amountContainer.className = 'number-likes ps-2 d-flex align-items-center'
        const number = document.createElement('span')
        number.className = 'me-1'
        number.id = 'num-likes'
        const likeWord = document.createElement('span')
        likeWord.id = 'like-word'
        let numberOfLikes = post.likes.length
        number.textContent = numberOfLikes
        likeWord.textContent = numberOfLikes === 1 ? 'like' : 'likes'
        amountContainer.appendChild(number)
        amountContainer.appendChild(likeWord)
        likeContainer.appendChild(amountContainer)

        const divCaption = document.createElement('div')
        divCaption.className = 'caption mx-3 mt-3'
        const pCaption = document.createElement('p')
        const spanCaption = document.createElement('span')
        spanCaption.classList.add('author')
        const userLink1 = userLink.cloneNode(true)
        spanCaption.appendChild(userLink1)
        pCaption.append(spanCaption, ` ${post.caption}`)
        divCaption.append(pCaption)

        const divDate = document.createElement('div')
        divDate.className = 'date ms-3 my-3'
        const pDate = document.createElement('p')
        pDate.textContent = `${post.pub_date}`
        divDate.append(pDate)

        divPost.append(divAuthorPost)
        divPost.append(divPhoto)
        divPost.append(likeContainer)
        divPost.append(divCaption)
        divPost.append(divDate)

        container.append(divPost)

        heart.addEventListener('click', () => {
            liked = !liked
            if (!liked) {
                fetch(`${window.location.origin}/app/likes/${post.id}/${authUserID}`, {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken'),
                        },
                    })
                    .then(response => {
                        if (response.ok) {
                            setHeart(heartSvg, liked)
                            adjustNumLikes(number, likeWord, -1)
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
                fetch(`${window.location.origin}/app/likes/${post.id}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken'),
                        },
                        body: JSON.stringify({'user_id': authUserID}),
                    })
                    .then(response => {
                        if (response.ok) {
                            setHeart(heartSvg, liked)
                            adjustNumLikes(number, likeWord, 1)
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
}

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