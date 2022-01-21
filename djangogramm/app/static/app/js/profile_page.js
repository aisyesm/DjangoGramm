"use strict"

const curScriptElement = document.currentScript

document.addEventListener("DOMContentLoaded", function() {
    let start = 0
    let offset = 9
    let userID = curScriptElement.getAttribute('user_id')
    let post_count = curScriptElement.getAttribute('post_count')
    const followData = JSON.parse(document.getElementById('follow-data').textContent)
    const authUserID = JSON.parse(document.getElementById('auth-user-id').textContent)
    let canFollow = followData['can_follow']

    getPosts(start, offset, userID)

    window.addEventListener('scroll', function() {
        let windowRelativeBottom = document.documentElement.getBoundingClientRect().bottom
        if (windowRelativeBottom < document.documentElement.clientHeight + 50) {
            start += offset
            if (start < post_count) {
                getPosts(start, offset, userID)
            }
        }
    })

    if (canFollow) {
        const bio = document.getElementById('bio')
        const btnFollow = document.createElement('button')
        const confirmUnfollow = document.getElementById('confirm-unfollow')
        bio.after(btnFollow)
        let isFollowing = followData['is_following']
        setFollowOption(btnFollow, isFollowing)
        btnFollow.addEventListener('click', () => {
            if (!isFollowing) {
                fetch(`${window.location.origin}/app/subscriptions/${authUserID}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: JSON.stringify({'followee_id': userID}),
                })
                .then(response => {
                    if (response.ok) {
                        setFollowOption(btnFollow, isFollowing=true)
                        adjustNumFollowers(1)
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
        confirmUnfollow.addEventListener('click', () => {
            fetch(`${window.location.origin}/app/subscriptions/${authUserID}/${userID}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                })
                .then(response => {
                    if (response.ok) {
                        setFollowOption(btnFollow, isFollowing=false)
                        adjustNumFollowers(-1)
                    }
                    else {
                        alert(`You request cannot be proceeded (error code ${response.status}), please reload the page`)
                    }
                })
                .catch((error) => {
                  alert(`There has been a problem with your fetch operation: ${error}`)
                });
        })
    }
})


function setFollowOption (btn, isFollowing) {
    if (!isFollowing) {
        btn.innerHTML = 'Follow'
        btn.className = 'action-btn btn btn-primary mb-4 mt-sm-2 mt-lg-3 px-4 px-md-5'
        btn.removeAttribute('data-bs-toggle')
        btn.removeAttribute('data-bs-target')
    }
    else {
        btn.innerHTML = 'Unfollow'
        btn.className = 'action-btn btn btn-danger mb-4 mt-sm-2 mt-lg-3 px-4 px-md-5'
        btn.setAttribute('data-bs-toggle', 'modal')
        btn.setAttribute('data-bs-target', '#unfollowModal')
    }
}


function adjustNumFollowers(delta) {
    let followersElem = document.getElementById('num-followers')
    let numFollowers = followersElem.textContent
    numFollowers = parseInt(numFollowers, 10)
    numFollowers += delta
    followersElem.textContent = numFollowers
    if (numFollowers === 1) {
        document.getElementById('id-followers').textContent = 'Follower'
    }
    else {
        document.getElementById('id-followers').textContent = 'Followers'
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


function getPosts (start, offset, userID) {
    fetch(`${window.location.origin}/app/posts?user_id=${userID}&offset=${offset}&start=${start}`)
    .then (response => response.json())
    .then (json => showPosts(json))
}


function showPosts (posts) {
    const userPosts = document.querySelector('.user_posts')
    posts.forEach(post => {
        const div = document.createElement('div')
        div.classList.add("post-area");
        const hyperlink = document.createElement('a')
        hyperlink.href = `${window.location.origin}/app/p/${post.id}`
        const img = document.createElement('img')
        img.src = post.image
        hyperlink.appendChild(img)
        div.appendChild(hyperlink)
        userPosts.append(div)
    })
}