import pytest

from app.matching.job_title import job_title, scale_of


@pytest.mark.parametrize("grade,title,scale", [
    ("تقني من الدرجة الثالثة - سُلمْ 9", "تقني", 9),
    ("تقني من الدرجة الرابعة - سُلمْ 8", "تقني", 8),
    ("مهندس دولة من الدرجة الأولى - سُلمْ 11", "مهندس دولة", 11),
    ("متصرف من الدرجة الثانية لفائدة كلية العلوم القانونية", "متصرف", None),
    ("متصرف من الدرجة الثالثة برئاسة جامعة الحسن الثاني", "متصرف", None),
    ("أستاذ محاضر من الدرجة أ - سُلمْ 11", "أستاذ محاضر", 11),
    ("ممرض من الدرجة الأولى - سُلمْ 10", "ممرض", 10),
    ("طبيب من الدرجة الأولى - سُلمْ 11", "طبيب", 11),
    ("توظيف متصرف من الدرجة الثالثة بكلية العلوم عين الشق", "متصرف", None),
    ("مكلف بإدارة المشاريع التقنية – التطوير والذكاء الاصطناعي", "مكلف بإدارة المشاريع التقنية", None),
    ("Technicien de 3ème grade - Echelle 9", "Technicien", 9),
    ("Administrateur 2ème grade - Echelle 11", "Administrateur", 11),
    ("Ingénieur d'Etat 1er grade", "Ingénieur d'Etat", None),
    ("Médecins premier grade - Echelle 11", "Médecins", 11),
    ("", None, None),
    (None, None, None),
])
def test_title_and_scale(grade, title, scale):
    assert job_title(grade) == title
    assert scale_of(grade) == scale


@pytest.mark.parametrize("title,family", [
    ("مهندس دولة", "مهندس"), ("مهندس معماري", "مهندس"), ("مكلفين", "مكلف"),
    ("مكلف بخدمة الزبناء", "مكلف"), ("المنسقة العامة للمجلات", "منسقة"),
    ("أستاذ محاضر", "أستاذ"), ("Techniciens", "Technicien"), (None, None),
])
def test_family(title, family):
    from app.matching.job_title import job_family
    assert job_family(title) == family


def test_count_word_is_dropped():
    assert job_title("منصبان (مهندس رئيس مشروع في البيئة وسائق)") == "مهندس رئيس مشروع"
