// Copyright 2020-2022 The MathWorks, Inc.
// Common copy functions for pong_msgs/PongScore
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
#include "pong_msgs/msg/pong_score.hpp"
#include "visibility_control.h"
#include "class_loader/multi_library_class_loader.hpp"
#include "ROS2PubSubTemplates.hpp"
class PONG_MSGS_EXPORT ros2_pong_msgs_msg_PongScore_common : public MATLABROS2MsgInterface<pong_msgs::msg::PongScore> {
  public:
    virtual ~ros2_pong_msgs_msg_PongScore_common(){}
    virtual void copy_from_struct(pong_msgs::msg::PongScore* msg, const matlab::data::Struct& arr, MultiLibLoader loader); 
    //----------------------------------------------------------------------------
    virtual MDArray_T get_arr(MDFactory_T& factory, const pong_msgs::msg::PongScore* msg, MultiLibLoader loader, size_t size = 1);
};
  void ros2_pong_msgs_msg_PongScore_common::copy_from_struct(pong_msgs::msg::PongScore* msg, const matlab::data::Struct& arr,
               MultiLibLoader loader) {
    try {
        //player_scored
        const matlab::data::TypedArray<int32_t> player_scored_arr = arr["player_scored"];
        msg->player_scored = player_scored_arr[0];
    } catch (matlab::data::InvalidFieldNameException&) {
        throw std::invalid_argument("Field 'player_scored' is missing.");
    } catch (matlab::Exception&) {
        throw std::invalid_argument("Field 'player_scored' is wrong type; expected a int32.");
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
        //event_type
        const matlab::data::CharArray event_type_arr = arr["event_type"];
        msg->event_type = event_type_arr.toAscii();
    } catch (matlab::data::InvalidFieldNameException&) {
        throw std::invalid_argument("Field 'event_type' is missing.");
    } catch (matlab::Exception&) {
        throw std::invalid_argument("Field 'event_type' is wrong type; expected a string.");
    }
    try {
        //winner
        const matlab::data::CharArray winner_arr = arr["winner"];
        msg->winner = winner_arr.toAscii();
    } catch (matlab::data::InvalidFieldNameException&) {
        throw std::invalid_argument("Field 'winner' is missing.");
    } catch (matlab::Exception&) {
        throw std::invalid_argument("Field 'winner' is wrong type; expected a string.");
    }
  }
  //----------------------------------------------------------------------------
  MDArray_T ros2_pong_msgs_msg_PongScore_common::get_arr(MDFactory_T& factory, const pong_msgs::msg::PongScore* msg,
       MultiLibLoader loader, size_t size) {
    auto outArray = factory.createStructArray({size,1},{"MessageType","player_scored","score_player1","score_player2","event_type","winner"});
    for(size_t ctr = 0; ctr < size; ctr++){
    outArray[ctr]["MessageType"] = factory.createCharArray("pong_msgs/PongScore");
    // player_scored
    auto currentElement_player_scored = (msg + ctr)->player_scored;
    outArray[ctr]["player_scored"] = factory.createScalar(currentElement_player_scored);
    // score_player1
    auto currentElement_score_player1 = (msg + ctr)->score_player1;
    outArray[ctr]["score_player1"] = factory.createScalar(currentElement_score_player1);
    // score_player2
    auto currentElement_score_player2 = (msg + ctr)->score_player2;
    outArray[ctr]["score_player2"] = factory.createScalar(currentElement_score_player2);
    // event_type
    auto currentElement_event_type = (msg + ctr)->event_type;
    outArray[ctr]["event_type"] = factory.createCharArray(currentElement_event_type);
    // winner
    auto currentElement_winner = (msg + ctr)->winner;
    outArray[ctr]["winner"] = factory.createCharArray(currentElement_winner);
    }
    return std::move(outArray);
  } 
class PONG_MSGS_EXPORT ros2_pong_msgs_PongScore_message : public ROS2MsgElementInterfaceFactory {
  public:
    virtual ~ros2_pong_msgs_PongScore_message(){}
    virtual std::shared_ptr<MATLABPublisherInterface> generatePublisherInterface(ElementType /*type*/);
    virtual std::shared_ptr<MATLABSubscriberInterface> generateSubscriberInterface(ElementType /*type*/);
    virtual std::shared_ptr<void> generateCppMessage(ElementType /*type*/, const matlab::data::StructArray& /* arr */, MultiLibLoader /* loader */, std::map<std::string,std::shared_ptr<MATLABROS2MsgInterfaceBase>>* /*commonObjMap*/);
    virtual matlab::data::StructArray generateMLMessage(ElementType  /*type*/ ,void*  /* msg */, MultiLibLoader /* loader */ , std::map<std::string,std::shared_ptr<MATLABROS2MsgInterfaceBase>>* /*commonObjMap*/);
};  
  std::shared_ptr<MATLABPublisherInterface> 
          ros2_pong_msgs_PongScore_message::generatePublisherInterface(ElementType /*type*/){
    return std::make_shared<ROS2PublisherImpl<pong_msgs::msg::PongScore,ros2_pong_msgs_msg_PongScore_common>>();
  }
  std::shared_ptr<MATLABSubscriberInterface> 
         ros2_pong_msgs_PongScore_message::generateSubscriberInterface(ElementType /*type*/){
    return std::make_shared<ROS2SubscriberImpl<pong_msgs::msg::PongScore,ros2_pong_msgs_msg_PongScore_common>>();
  }
  std::shared_ptr<void> ros2_pong_msgs_PongScore_message::generateCppMessage(ElementType /*type*/, 
                                           const matlab::data::StructArray& arr,
                                           MultiLibLoader loader,
                                           std::map<std::string,std::shared_ptr<MATLABROS2MsgInterfaceBase>>* commonObjMap){
    auto msg = std::make_shared<pong_msgs::msg::PongScore>();
    ros2_pong_msgs_msg_PongScore_common commonObj;
    commonObj.mCommonObjMap = commonObjMap;
    commonObj.copy_from_struct(msg.get(), arr[0], loader);
    return msg;
  }
  matlab::data::StructArray ros2_pong_msgs_PongScore_message::generateMLMessage(ElementType  /*type*/ ,
                                                    void*  msg ,
                                                    MultiLibLoader  loader ,
                                                    std::map<std::string,std::shared_ptr<MATLABROS2MsgInterfaceBase>>*  commonObjMap ){
    ros2_pong_msgs_msg_PongScore_common commonObj;	
    commonObj.mCommonObjMap = commonObjMap;	
    MDFactory_T factory;
    return commonObj.get_arr(factory, (pong_msgs::msg::PongScore*)msg, loader);			
 }
#include "class_loader/register_macro.hpp"
// Register the component with class_loader.
// This acts as a sort of entry point, allowing the component to be discoverable when its library
// is being loaded into a running process.
CLASS_LOADER_REGISTER_CLASS(ros2_pong_msgs_msg_PongScore_common, MATLABROS2MsgInterface<pong_msgs::msg::PongScore>)
CLASS_LOADER_REGISTER_CLASS(ros2_pong_msgs_PongScore_message, ROS2MsgElementInterfaceFactory)
#ifdef _MSC_VER
#pragma warning(pop)
#else
#pragma GCC diagnostic pop
#endif //_MSC_VER