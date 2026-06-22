function [data, info] = pongScore
%PongScore gives an empty data for pong_msgs/PongScore
% Copyright 2019-2021 The MathWorks, Inc.
data = struct();
data.MessageType = 'pong_msgs/PongScore';
[data.player_scored, info.player_scored] = ros.internal.ros2.messages.ros2.default_type('int32',1,0);
[data.score_player1, info.score_player1] = ros.internal.ros2.messages.ros2.default_type('int32',1,0);
[data.score_player2, info.score_player2] = ros.internal.ros2.messages.ros2.default_type('int32',1,0);
[data.event_type, info.event_type] = ros.internal.ros2.messages.ros2.char('string',1,NaN,0);
[data.winner, info.winner] = ros.internal.ros2.messages.ros2.char('string',1,NaN,0);
info.MessageType = 'pong_msgs/PongScore';
info.constant = 0;
info.default = 0;
info.maxstrlen = NaN;
info.MaxLen = 1;
info.MinLen = 1;
info.MatPath = cell(1,5);
info.MatPath{1} = 'player_scored';
info.MatPath{2} = 'score_player1';
info.MatPath{3} = 'score_player2';
info.MatPath{4} = 'event_type';
info.MatPath{5} = 'winner';
