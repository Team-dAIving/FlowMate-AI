from types import SimpleNamespace
from app.services.meeting_create_guard import enforce_explicit_task_creates


def req(text='로그인 API 테스트 업무도 추가하겠습니다.', existing=()):
    return SimpleNamespace(
        existingTasks=[SimpleNamespace(title=t) for t in existing],
        transcript=SimpleNamespace(segments=[SimpleNamespace(segmentId='seg-2', text=text)]),
    )


def test_promotes_matching_review_to_create():
    data = {'actionItems':[{'actionType':'NEEDS_REVIEW','title':'로그인 API 테스트 업무 추가',
                            'evidenceSegmentIds':['seg-2'],'requiresReview':True}]}
    result = enforce_explicit_task_creates(req(), data)
    assert len(result['actionItems']) == 1
    action = result['actionItems'][0]
    assert action['actionType'] == 'CREATE'
    assert action['title'] == '로그인 API 테스트'
    assert action['requiresReview'] is True
    assert action['evidenceSegmentIds'] == ['seg-2']
    assert action['targetTaskId'] is None


def test_adds_missing_create():
    data = {'actionItems': []}
    assert enforce_explicit_task_creates(req(), data)['actionItems'][0]['actionType'] == 'CREATE'


def test_existing_task_never_promoted():
    data = {'actionItems':[{'actionType':'NEEDS_REVIEW','title':'로그인 API 테스트 업무 추가',
                            'evidenceSegmentIds':['seg-2']}]}
    enforce_explicit_task_creates(req(existing=['로그인 API 테스트']), data)
    assert data['actionItems'][0]['actionType'] == 'NEEDS_REVIEW'


def test_uncertain_not_promoted():
    for text in ['로그인 API 테스트 업무도 추가할까요?', '로그인 API 테스트 추가를 검토합시다.',
                 '로그인 API 테스트는 추가하지 맙시다.']:
        data = {'actionItems': []}
        enforce_explicit_task_creates(req(text=text), data)
        assert data['actionItems'] == []


def test_no_duplicate_create():
    data = {'actionItems':[{'actionType':'CREATE','title':'로그인 API 테스트',
                            'evidenceSegmentIds':['seg-2']}]}
    enforce_explicit_task_creates(req(), data)
    assert len(data['actionItems']) == 1


def test_does_not_promote_unrelated_review():
    data = {'actionItems':[{'actionType':'NEEDS_REVIEW','title':'보안 정책',
                            'evidenceSegmentIds':['seg-2']}]}
    enforce_explicit_task_creates(req(), data)
    assert data['actionItems'][0]['actionType'] == 'NEEDS_REVIEW'
