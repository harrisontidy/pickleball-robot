# Autonomous Pickleball Robot

An autonomous robot being developed to play pickleball against a human. It is designed to watch an incoming shot, move into position, and swing a paddle to return the ball across the net.

The goal is to create a practice partner that can react to your shots and keep a rally going.

## Playing a rally

The planned vision system uses a camera and YOLO object detection to locate the pickleball and follow its movement. From successive observations, the robot estimates where the ball is heading and where it needs to meet it.

The mobile base moves into position while the arm adjusts the paddle's angle. The swing mechanism is designed to time the stroke with the ball's arrival, return the shot, and bring the paddle back into position for the next ball.

The intended rally follows a continuous cycle:

1. Detect the incoming ball.
2. Track its path and estimate an interception point.
3. Move into position and line up the paddle.
4. Swing to return the shot.
5. Reset and watch for the next ball.

## Manual control

The robot also has a phone control page for driving, adjusting the paddle joints, and triggering swing sequences. These controls let the drive and paddle movements be tested individually while the autonomous rally system is developed.
