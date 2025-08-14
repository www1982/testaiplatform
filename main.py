#!/usr/bin/env python
"""
ONI AI Platform - Main Entry Point

This script provides a unified entry point for the entire platform.
It can launch either the desktop GUI debugger or the headless training engine.
"""

import sys
import argparse
import logging
import asyncio
from pathlib import Path


def setup_logging(verbose: bool = False):
    """Configure logging for the application"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('oni_ai_platform.log')
        ]
    )


def run_gui():
    """Launch the desktop GUI debugger"""
    from desktop_debugger.main import main as gui_main
    gui_main()


def run_training(agent_type: str, reward_function: str):
    """Launch the training engine"""
    from training_engine.main_loop import main as training_main
    
    # Prepare arguments for training
    sys.argv = [
        'training',
        '--agent', agent_type,
        '--reward', reward_function
    ]
    
    asyncio.run(training_main())


def main():
    parser = argparse.ArgumentParser(
        description="ONI AI Platform - Control and train AI agents for Oxygen Not Included",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s gui                    # Launch the desktop GUI debugger
  %(prog)s train --agent drl      # Start training with DRL agent
  %(prog)s train --agent rule     # Start training with rule-based agent
        """
    )
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')
    
    subparsers = parser.add_subparsers(dest='mode', help='Operating mode')
    
    # GUI mode
    gui_parser = subparsers.add_parser('gui', help='Launch desktop GUI debugger')
    
    # Training mode
    train_parser = subparsers.add_parser('train', help='Launch training engine')
    train_parser.add_argument('--agent', choices=['rule', 'drl'], default='rule',
                            help='Agent type to use for training')
    train_parser.add_argument('--reward', 
                            choices=['survival', 'efficiency', 'expansion', 'balanced'],
                            default='balanced',
                            help='Reward function to use')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Default to GUI if no mode specified
    if args.mode is None:
        args.mode = 'gui'
    
    try:
        if args.mode == 'gui':
            logger.info("Launching GUI debugger...")
            run_gui()
        elif args.mode == 'train':
            logger.info(f"Starting training with {args.agent} agent and {args.reward} reward...")
            run_training(args.agent, args.reward)
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()