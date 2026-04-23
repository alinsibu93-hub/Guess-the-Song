import React from 'react';
import './MultipleChoice.css';

/**
 * Grid of answer choices for multiple_choice mode.
 * Submit happens on card click — no separate Submit button.
 *
 * Props:
 *   choices  – array of { title: string, artist: string }
 *   onSelect – callback(choiceIndex: number) — fires immediately on click
 *   disabled – true while submitting or outside AWAITING_GUESS state
 *   selected – index of the clicked choice (null before any click)
 */
export default function MultipleChoice({ choices, onSelect, disabled, selected }) {
  return (
    <div className="multiple-choice">
      {choices.map((choice, index) => {
        const isSelected = selected === index;
        return (
          <button
            key={`${choice.title}__${index}`}
            className={`choice-btn${isSelected ? ' choice-btn--selected' : ''}`}
            onClick={() => onSelect(index)}
            // Disable all cards once one is clicked (prevents double-submit).
            disabled={disabled || selected !== null}
            type="button"
            aria-pressed={isSelected}
          >
            <span className="choice-title">{choice.title}</span>
            <span className="choice-artist">{choice.artist}</span>
          </button>
        );
      })}
    </div>
  );
}
