from datetime import date
from types import SimpleNamespace

from app.services.meeting_update_guard import enforce_explicit_due_date_updates, resolve_date


def req(text='DB 설계 마감일을 다음 주 월요일로 변경합시다.'):
    return SimpleNamespace(
        meetingDate=date(2026, 11, 23),
        existingTasks=[SimpleNamespace(taskId=502, title='DB 설계')],
        transcript=SimpleNamespace(segments=[SimpleNamespace(segmentId='seg-1', text=text)]),
    )


def test_next_monday():
    assert resolve_date('다음 주 월요일', date(2026, 11, 23)) == date(2026, 11, 30)


def test_missing_update_is_added_and_proposal_decision_removed():
    output = {
        'decisions': [{'content': 'DB 설계 마감일 변경', 'evidenceSegmentIds': ['seg-1']}],
        'unresolvedItems': [],
        'actionItems': [{'actionType':'CREATE', 'title':'로그인 API 테스트', 'evidenceSegmentIds':['seg-2']}],
    }
    result = enforce_explicit_due_date_updates(req(), output)
    assert result['decisions'] == []
    updates = [a for a in result['actionItems'] if a['actionType'] == 'UPDATE']
    assert len(updates) == 1
    assert updates[0]['targetTaskId'] == 502
    assert updates[0]['changes'] == {'dueDate': '2026-11-30'}
    assert updates[0]['evidenceSegmentIds'] == ['seg-1']
    assert updates[0]['requiresReview'] is True


def test_does_not_duplicate_existing_update():
    output = {'actionItems':[{'actionType':'UPDATE','targetTaskId':502,'changes':{'dueDate':'2026-11-30'}}]}
    assert len(enforce_explicit_due_date_updates(req(), output)['actionItems']) == 1


def test_does_not_invent_date_or_task():
    output = {'actionItems': []}
    enforce_explicit_due_date_updates(req('DB 설계 마감일 변경을 검토합시다.'), output)
    assert output['actionItems'] == []
    enforce_explicit_due_date_updates(req('없는 업무 마감일을 다음 주 월요일로 변경합시다.'), output)
    assert output['actionItems'] == []


def test_does_not_update_when_negated():
    output = {'actionItems': []}
    enforce_explicit_due_date_updates(req('DB 설계 마감일은 다음 주 월요일로 변경하지 맙시다.'), output)
    assert output['actionItems'] == []
