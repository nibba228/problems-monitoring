function makeSeen(userId, problemId, topicName){
    fetch('/make-seen', {
        method: 'POST',
        body: JSON.stringify({
            userId: userId,
            problemId: problemId,
            topicName: topicName
        })
    }).then((_res) => {
        window.location.href = '/';
    });
}