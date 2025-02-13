from typing import Any, Counter

from template_start import run_template_matching


def analyze_events_and_formations(events: Any, match_id: int
                                  ) -> dict[Any, Any]:
    """
      Analyzes events and defensive formations at specific times
    in the game.

    Args:
        events (pd.DataFrame): DataFrame with event data
        sequences (pd.DataFrame): DataFrame with sequence data
        match_id (int): ID of the match to be analyzed

    Returns:
        dict: Dictionary with statistics on events and formations
        per phase
    """
    # Template Matching ausführen
    phase_results = run_template_matching(match_id)

    # Ergebnisdictionary initialisieren
    analysis_results: dict[Any, Any]
    analysis_results = {
        phase: {'events': [], 'formations': []} for phase in range(5)
    }
    for event in events.values:
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
    total_shots = 0
    successful_goals = 0
    for phase in analysis_results:
        for event, count in analysis_results[phase]['event_statistics'
                                                    ].items():
            if event in ['shot_blocked', 'shot_saved', 'shot_off_target',
                         'score_change']:
                total_shots += count
                if event == 'score_change':
                    successful_goals += count

        if total_shots > 0:
            goal_success_rate = (successful_goals / total_shots) * 100
        else:
            goal_success_rate = 0

        analysis_results[phase]['goal_success_rate'] = goal_success_rate

    return analysis_results
