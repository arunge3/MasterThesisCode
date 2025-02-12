from typing import Any, Counter

from template_start import run_template_matching


def analyze_events_and_formations(events: Any, match_id: int
                                  ) -> dict[Any, Any]:
    """
    Analysiert Events und Abwehrformationen zu bestimmten Zeitpunkten
    im Spiel.

    Args:
        events (pd.DataFrame): DataFrame mit Event-Daten
        sequences (pd.DataFrame): DataFrame mit Sequenz-Daten
        match_id (int): ID des zu analysierenden Spiels

    Returns:
        dict: Dictionary mit Statistiken über Events und Formationen
        pro Phase
    """
    # Template Matching ausführen
    phase_results = run_template_matching(match_id)

    # Ergebnisdictionary initialisieren
    analysis_results: dict[Any, Any]
    analysis_results = {
        phase: {'events': [], 'formations': []} for phase in range(5)
    }
# TODO Funktioniert noch nicht, debuggen
    for _, event in events.iterrows():
        event_time = event[24]
        event_type = event[0]

        current_phase = None
        for phase_info in phase_results:

            if phase_info['start'] <= event_time <= phase_info['end']:
                current_phase = phase_info['phase_type']
                formation = phase_info['formation']
                break

        if current_phase is not None:
            analysis_results[current_phase]['events'].append(event_type)
            analysis_results[current_phase]['formations'].append(formation)

    # Zusammenfassung erstellen
    for phase in analysis_results:
        events_count = Counter(analysis_results[phase]['events'])
        formations_count = Counter(analysis_results[phase]['formations'])
        analysis_results[phase] = {
            'event_statistics': dict(events_count),
            'formation_statistics': dict(formations_count)
        }

    return analysis_results
