// Copyright 2020-2022 The MathWorks, Inc.
// Common copy functions for pong_msgs/PongGameState
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4100)
#pragma warning(disable : 4265)
#pragma warning(disable : 4456)
#pragma warning(disable : 4458)
#pragma warning(disable : 4946)
#pragma warning(disable : 4244)
#else
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wpedantic"
#pragma GCC diagnostic ignored "-Wunused-local-typedefs"
#pragma GCC diagnostic ignored "-Wredundant-decls"
#pragma GCC diagnostic ignored "-Wnon-virtual-dtor"
#pragma GCC diagnostic ignored "-Wdelete-non-virtual-dtor"
#pragma GCC diagnostic ignored "-Wunused-parameter"
#pragma GCC diagnostic ignored "-Wunused-variable"
#pragma GCC diagnostic ignored "-Wshadow"
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"
#endif //_MSC_VER
#include "rclcpp/rclcpp.hpp"
#include "pong_msgs/msg/pong_game_state.hpp"
#include "visibility_control.h"
#include "class_loader/multi_library_class_loader.hpp"
#include "ROS2PubSubTemplates.hpp"
class PONG_MSGS_EXPORT ros2_pong_msgs_msg_PongGameState_common : public MATLABROS2MsgInterface<pong_msgs::msg::PongGameState> {
  public:
    virtual ~ros2_pong_msgs_msg_PongGameState_common(){}
    virtual void copy_from_struct(pong_msgs::msg::PongGameState* msg, const matlab::data::Struct& arr, MultiLibLoader loader); 
    //----------------------------------------------------------------------------
    virtual MDArray_T get_arr(MDFactory_T& factory, const pong_msgs::msg::PongGameState* msg, MultiLibLoader loader, size_t size = 1);
};
  void ros2_pong_msgs_msg_PongGameState_common::copy_from_struct(pong_msgs::msg::PongGameState* msg, const matlab::data::Struct& arr,
               MultiLibLoader loader) {
    try {
        //ball_x
        const matlab::data::TypedArray<float> ball_x_arr = arr["ball_x"];
        msg->ball_x = ball_x_arr[0];
    } catch (matlab::data::InvalidFieldNameException&) {
        throw std::invalid_argument("Field 'ball_x' is missing.");
    } catch (matlab::Exception&) {
        throw std::invalid_argument("Field 'ball_x' is wrong type; expected a single.");
    }
    try {
        //ball_y
        const matlab::data::TypedArray<float> ball_y_arr = arr["ball_y"];
        msg->ball_y = ball_y_arr[0];
    } catch (matlab::data::InvalidFieldNameException&) {
        throw std::invalid_argument("Field 'ball_y' is missing.");
    } catch (matlab::Exception&) {
        throw std::invalid_argument("Field 'ball_y' is wrong type; expected a single.");
    }
    try {
        //ball_vel_x
        const matlab::data::TypedArray<float> ball_vel_x_arr = arr["ball_vel_x"];
        msg->ball_vel_x = ball_vel_x_arr[0];
    } catch (matlab::data::InvalidFieldNameException&) {
        throw std::invalid_argument("Field 'ball_vel_x' is missing.");
    } catch (matlab::Exception&) {
        throw std::invalid_argument("Field 'ball_vel_x' is wrong type; expected a single.");
    }
    try {
        //ball_vel_y
        const matlab::data::TypedArray<float> ball_vel_y_arr = arr["ball_vel_y"];
        msg->ball_vel_y = ball_vel_y_arr[0];
    } catch (matlab::data::InvalidFieldNameException&) {
        throw std::invalid_argument("Field 'ball_vel_y' is missing.");
    } catch (matlab::Exception&) {
        throw std::invalid_argument("Field 'ball_vel_y' is wrong type; expected a single.");
    }
    try {
        //paddle1_y
        const matlab::data::TypedArray<float> paddle1_y_arr = arr["paddle1_y"];
        msg->paddle1_y = paddle1_y_arr[0];
    } catch (matlab::data::InvalidFieldNameException&) {
        throw std::invalid_argument("Field 'paddle1_y' is missing.");
    } catch (matlab::Exception&) {
        throw std::invalid_argument("Field 'paddle1_y' is wrong type; expected a single.");
    }
    try {
        //paddle2_y
        const matlab::data::TypedArray<float> paddle2_y_arr = arr["paddle2_y"];
        msg->paddle2_y = paddle2_y_arr[0];
    } catch (matlab::data::InvalidFieldNameException&) {
        throw std::invalid_argument("Field 'paddle2_y' is missing.");
    } catch (matlab::Exception&) {
        throw std::invalid_argument("Field 'paddle2_y' is wrong type; expected a single.");
    }
    try {
        //score_player1
        const matlab::data::TypedArray<int32_t> score_player1_arr = arr["score_player1"];
        msg->score_player1 = score_player1_arr[0];
    } catch (matlab::data::InvalidFieldNameException&) {
        throw std::invalid_argument("Field 'score_player1' is missing.");
    } catch (matlab::Exception&) {
        throw std::invalid_argument("Field 'score_player1' is wrong type; expected a int32.");
    }
    try {
        //score_player2
        const matlab::data::TypedArray<int32_t> score_player2_arr = arr["score_player2"];
        msg->score_player2 = score_player2_arr[0];
    } catch (matlab::data::InvalidFieldNameException&) {
        throw std::invalid_argument("Field 'score_player2' is missing.");
    } catch (matlab::Exception&) {
        throw std::invalid_argument("Field 'score_player2' is wrong type; expected a int32.");
    }
    try {
        //game_status
        const matlab::data::TypedArray<int32_t> game_status_arr = arr["game_status"];
        msg->game_status = game_status_arr[0];
    } catch (matlab::data::InvalidFieldNameException&) {
        throw std::invalid_argument("Field 'game_status' is missing.");
    } catch (matlab::Exception&) {
        throw std::invalid_argument("Field 'game_status' is wrong type; expected a int32.");
    }
  }
  //----------------------------------------------------------------------------
  MDArray_T ros2_pong_msgs_msg_PongGameState_common::get_arr(MDFactory_T& factory, const pong_msgs::msg::PongGameState* msg,
       MultiLibLoader loader, size_t size) {
    auto outArray = factory.createStructArray({size,1},{"MessageType","ball_x","ball_y","ball_vel_x","ball_vel_y","paddle1_y","paddle2_y","score_player1","score_player2","game_status"});
    for(size_t ctr = 0; ctr < size; ctr++){
    outArray[ctr]["MessageType"] = factory.createCharArray("pong_msgs/PongGameState");
    // ball_x
    auto currentElement_ball_x = (msg + ctr)->ball_x;
    outArray[ctr]["ball_x"] = factory.createScalar(currentElement_ball_x);
    // ball_y
    auto currentElement_ball_y = (msg + ctr)->ball_y;
    outArray[ctr]["ball_y"] = factory.createScalar(currentElement_ball_y);
    // ball_vel_x
    auto currentElement_ball_vel_x = (msg + ctr)->ball_vel_x;
    outArray[ctr]["ball_vel_x"] = factory.createScalar(currentElement_ball_vel_x);
    // ball_vel_y
    auto currentElement_ball_vel_y = (msg + ctr)->ball_vel_y;
    outArray[ctr]["ball_vel_y"] = factory.createScalar(currentElement_ball_vel_y);
    // paddle1_y
    auto currentElement_paddle1_y = (msg + ctr)->paddle1_y;
    outArray[ctr]["paddle1_y"] = factory.createScalar(currentElement_paddle1_y);
    // paddle2_y
    auto currentElement_paddle2_y = (msg + ctr)->paddle2_y;
    outArray[ctr]["paddle2_y"] = factory.createScalar(currentElement_paddle2_y);
    // score_player1
    auto currentElement_score_player1 = (msg + ctr)->score_player1;
    outArray[ctr]["score_player1"] = factory.createScalar(currentElement_score_player1);
    // score_player2
    auto currentElement_score_player2 = (msg + ctr)->score_player2;
    outArray[ctr]["score_player2"] = factory.createScalar(currentElement_score_player2);
    // game_status
    auto currentElement_game_status = (msg + ctr)->game_status;
    outArray[ctr]["game_status"] = factory.createScalar(currentElement_game_status);
    }
    return std::move(outArray);
  } 
class PONG_MSGS_EXPORT ros2_pong_msgs_PongGameState_message : public ROS2MsgElementInterfaceFactory {
  public:
    virtual ~ros2_pong_msgs_PongGameState_message(){}
    virtual std::shared_ptr<MATLABPublisherInterface> generatePublisherInterface(ElementType /*type*/);
    virtual std::shared_ptr<MATLABSubscriberInterface> generateSubscriberInterface(ElementType /*type*/);
    virtual std::shared_ptr<void> generateCppMessage(ElementType /*type*/, const matlab::data::StructArray& /* arr */, MultiLibLoader /* loader */, std::map<std::string,std::shared_ptr<MATLABROS2MsgInterfaceBase>>* /*commonObjMap*/);
    virtual matlab::data::StructArray generateMLMessage(ElementType  /*type*/ ,void*  /* msg */, MultiLibLoader /* loader */ , std::map<std::string,std::shared_ptr<MATLABROS2MsgInterfaceBase>>* /*commonObjMap*/);
};  
  std::shared_ptr<MATLABPublisherInterface> 
          ros2_pong_msgs_PongGameState_message::generatePublisherInterface(ElementType /*type*/){
    return std::make_shared<ROS2PublisherImpl<pong_msgs::msg::PongGameState,ros2_pong_msgs_msg_PongGameState_common>>();
  }
  std::shared_ptr<MATLABSubscriberInterface> 
         ros2_pong_msgs_PongGameState_message::generateSubscriberInterface(ElementType /*type*/){
    return std::make_shared<ROS2SubscriberImpl<pong_msgs::msg::PongGameState,ros2_pong_msgs_msg_PongGameState_common>>();
  }
  std::shared_ptr<void> ros2_pong_msgs_PongGameState_message::generateCppMessage(ElementType /*type*/, 
                                           const matlab::data::StructArray& arr,
                                           MultiLibLoader loader,
                                           std::map<std::string,std::shared_ptr<MATLABROS2MsgInterfaceBase>>* commonObjMap){
    auto msg = std::make_shared<pong_msgs::msg::PongGameState>();
    ros2_pong_msgs_msg_PongGameState_common commonObj;
    commonObj.mCommonObjMap = commonObjMap;
    commonObj.copy_from_struct(msg.get(), arr[0], loader);
    return msg;
  }
  matlab::data::StructArray ros2_pong_msgs_PongGameState_message::generateMLMessage(ElementType  /*type*/ ,
                                                    void*  msg ,
                                                    MultiLibLoader  loader ,
                                                    std::map<std::string,std::shared_ptr<MATLABROS2MsgInterfaceBase>>*  commonObjMap ){
    ros2_pong_msgs_msg_PongGameState_common commonObj;	
    commonObj.mCommonObjMap = commonObjMap;	
    MDFactory_T factory;
    return commonObj.get_arr(factory, (pong_msgs::msg::PongGameState*)msg, loader);			
 }
#include "class_loader/register_macro.hpp"
// Register the component with class_loader.
// This acts as a sort of entry point, allowing the component to be discoverable when its library
// is being loaded into a running process.
CLASS_LOADER_REGISTER_CLASS(ros2_pong_msgs_msg_PongGameState_common, MATLABROS2MsgInterface<pong_msgs::msg::PongGameState>)
CLASS_LOADER_REGISTER_CLASS(ros2_pong_msgs_PongGameState_message, ROS2MsgElementInterfaceFactory)
#ifdef _MSC_VER
#pragma warning(pop)
#else
#pragma GCC diagnostic pop
#endif //_MSC_VER