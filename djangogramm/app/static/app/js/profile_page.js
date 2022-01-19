"use strict"

const curScriptElement = document.currentScript

document.addEventListener("DOMContentLoaded", function() {
    let start = 0
    let offset = 9
    let user_id = curScriptElement.getAttribute('user_id')
    let post_count = curScriptElement.getAttribute('post_count')
    const followData = JSON.parse(document.getElementById('follow-data').textContent)
    let canFollow = followData['can_follow']

    getPosts(start, offset, user_id)

    window.addEventListener('scroll', function() {
        let windowRelativeBottom = document.documentElement.getBoundingClientRect().bottom
        if (windowRelativeBottom < document.documentElement.clientHeight + 50) {
            start += offset
            if (start < post_count) {
                getPosts(start, offset, user_id)
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
                // fetch(`${window.location.origin}/app/subscriptions/${followee_id}/${follower_id}`, {
                //     method: 'POST',
                // }).then(response => response.json())
                //     .then(data => console.log(data))
                setFollowOption(btnFollow, isFollowing=true)
            }
        })
        confirmUnfollow.addEventListener('click', () => {
            // fetch(`${window.location.origin}/app/subscriptions/${followee_id}/${follower_id}`, {
                //     method: 'DELETE',
                // }).then(response => response.json())
                //     .then(data => console.log(data))
            setFollowOption(btnFollow, isFollowing=false)
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


function getPosts (start, offset, user_id) {
    fetch(`${window.location.origin}/app/posts?user_id=${user_id}&offset=${offset}&start=${start}`)
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