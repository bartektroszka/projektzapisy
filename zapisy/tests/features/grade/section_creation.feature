Feature: User with privileges wants to create a section.
    
    Scenario: Preparations
        Given I start new scenario for "grade"
        And the grading protocol is "off"
    
    Scenario: Employee creates a simple section
        Given I am logged in with "employee" privileges
        And I am on grade main page
        When I follow "Zarządzaj ankietami"
        And I follow "Lista sekcji"
        And I press "Utwórz nową"
        And I fill in "section-title" with "Sekcja przykładowego pracownika"
        And I press "Dodaj pytanie" 
        And I fill in "poll[question][1][title]" with "Jak podobał Ci się mój przedmiot?"
        And I press "Zapisz" 
        Then I should see "Sekcja dodana"
    
    Scenario: Administrator creates a simple section
        Given I am logged in with "administrator" privileges
        And I am on grade main page
        When I follow "Zarządzaj ankietami"
        And I follow "Lista sekcji"
        And I press "Utwórz nową"
        And I fill in "section-title" with "Sekcja administratora"
        And I press "Dodaj pytanie" 
        And I fill in "poll[question][1][title]" with "Jak podobała Ci się moja praca?"
        And I press "Zapisz" 
        Then I should see "Sekcja dodana"    
    
    Scenario: Administrator creates a more complex section with many different types of questions
        Given I am logged in with "administrator" privileges
        And I am on grade main page
        When I follow "Zarządzaj ankietami"
        And I follow "Lista sekcji"
        And I press "Utwórz nową"
        And I fill in "section-title" with "Sekcja administratora - złożona"
        And I press "Dodaj pytanie" 
        And I fill in "poll[question][1][title]" with "Jak podobała Ci oferta w tym semestrze?"
        And I select "poll[question][1][formtype]" as "Pytanie otwarte"
        And I press visible "Gotowe"
        And I press "Dodaj pytanie" 
        And I fill in "poll[question][2][title]" with "Czy była dość bogata?"
        And I select "poll[question][2][formtype]" as "Pytanie jednokrotnego wyboru"
        And I fill in "poll[question][2][answers][1]" with "tak"
        And I press visible "Dodaj odpowiedź" 
        And I fill in "poll[question][2][answers][2]" with "trudno powiedzieć"
        And I press visible "Dodaj odpowiedź" 
        And I fill in "poll[question][2][answers][3]" with "nie"
        And I press visible "Gotowe"
        And I press "Dodaj pytanie" 
        And I fill in "poll[question][3][title]" with "Czego było za mało?"
        And I select "poll[question][3][formtype]" as "Pytanie wielokrotnego wyboru"
        And I fill in "poll[question][3][answers][1]" with "Algorytmów"
        And I press visible "Dodaj odpowiedź"
        And I fill in "poll[question][3][answers][2]" with "Sieci"
        And I press visible "Dodaj odpowiedź" 
        And I fill in "poll[question][3][answers][3]" with "Kryptografii"
        And I press visible "Gotowe"
        And I press "Dodaj pytanie" 
        And I fill in "poll[question][4][title]" with "Czego było za dużo?"
        And I select "poll[question][4][formtype]" as "Pytanie wielokrotnego wyboru"
        And I fill in "poll[question][4][answers][1]" with "Algorytmów"
        And I press visible "Dodaj odpowiedź" 
        And I fill in "poll[question][4][answers][2]" with "Sieci"
        And I press visible "Dodaj odpowiedź" 
        And I fill in "poll[question][4][answers][3]" with "Kryptografii"
        And I check "poll[question][4][hasOther]"
        And I press visible "Gotowe"
        And I press "Zapisz"    
        Then I should see "Sekcja dodana"    
            
    Scenario: Administrator creates a section with opening question
        Given I am logged in with "administrator" privileges
        And I am on grade main page
        When I follow "Zarządzaj ankietami"
        And I follow "Lista sekcji"
        And I press "Utwórz nową"
        And I fill in "section-title" with "Sekcja administratora - pytanie wiodące"
        And I check "poll[leading]"
        And I fill in "poll[question][0][title]" with "Czy podobała Ci oferta w tym semestrze?"
        And I fill in "poll[question][0][answers][1]" with "tak"
        And I press visible "Dodaj odpowiedź" 
        And I fill in "poll[question][0][answers][2]" with "trudno powiedzieć"
        And I press visible "Dodaj odpowiedź" 
        And I fill in "poll[question][0][answers][3]" with "nie"
        And I check "poll[question][0][hideOn][]" with value "3"
        And I press visible "Gotowe"        
        And I press "Dodaj pytanie" 
        And I fill in "poll[question][1][title]" with "Czy była dość bogata?"
        And I select "poll[question][1][formtype]" as "Pytanie jednokrotnego wyboru"
        And I fill in "poll[question][1][answers][1]" with "tak"   
        And I press visible "Dodaj odpowiedź" 
        And I fill in "poll[question][1][answers][2]" with "trudno powiedzieć"
        And I press visible "Dodaj odpowiedź" 
        And I fill in "poll[question][1][answers][3]" with "nie"
        And I press visible "Gotowe"         
        And I press "Zapisz"         
        Then I should see "Sekcja dodana" 
    
    Scenario: Student enters the section creation page
        Given I am logged in with "student" privileges
        And I am on grade main page    
        When I go to /grade/poll/managment/sections_list
        Then I should see "Zaloguj"
    
    Scenario: Administrator tries to create section with no questions
        Given I am logged in with "administrator" privileges
        And I am on grade main page
        When I follow "Zarządzaj ankietami"
        And I follow "Lista sekcji"
        And I press "Utwórz nową"
        And I fill in "section-title" with "Sekcja administratora"
        And I press "Zapisz"
        Then I should see "Sekcja nie zawiera pytań"
            
    Scenario: Administrator tries to create section without a title
        Given I am logged in with "administrator" privileges
        And I am on grade main page
        When I follow "Zarządzaj ankietami"
        And I follow "Lista sekcji"
        And I press "Utwórz nową"
        And I press "Dodaj pytanie" 
        And I fill in "poll[question][1][title]" with "Jak podobała Ci się moja praca?"
        And I press "Zapisz"
        Then I should see "To pole jest wymagane."
    
    Scenario Outline: Administrator tries to add a question without a question text
        Given I am logged in with "administrator" privileges
        And I am on grade main page
        When I follow "Zarządzaj ankietami"
        And I follow "Lista sekcji"
        And I press "Utwórz nową"
        And I fill in "section-title" with "Sekcja administratora"         
        And I press "Dodaj pytanie" 
        And I select "poll[question][1][formtype]" as <typ_pytania>
        And I press "Zapisz"
        Then I should see "To pole jest wymagane."
        
    Examples:
        | typ_pytania |
        | "Pytanie otwarte" |
        | "Pytanie jednokrotnego wyboru" |
        | "Pytanie wielokrotnego wyboru" |
    
    Scenario Outline: Administrator tries to add a choice question with no choices
        Given I am logged in with "administrator" privileges
        And I am on grade main page
        When I follow "Zarządzaj ankietami"
        And I follow "Lista sekcji"
        And I press "Utwórz nową"
        And I fill in "section-title" with "Sekcja administratora"
        And I press "Dodaj pytanie" 
        And I select "poll[question][1][formtype]" as <typ_pytania>
        And I fill in "poll[question][1][title]" with "Treść pytania"
        And I press "Zapisz"
        Then I should see "To pole jest wymagane."

    Examples:
        | typ_pytania |
        | "Pytanie jednokrotnego wyboru" |
        | "Pytanie wielokrotnego wyboru" |

    Scenario: While grading protocol is active, the administrator tries to create a section
        Given I start new scenario for "grade"
        And the grading protocol is "on"
        And I am logged in with "administrator" privileges
        And I am on grade main page    
        When I go to /grade/poll/managment/sections_list
        Then I should see "Ocena zajęć jest otwarta; operacja nie jest w tej chwili dozwolona"
    